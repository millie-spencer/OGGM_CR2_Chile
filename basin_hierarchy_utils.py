"""
basin_hierarchy_utils.py

Computes basin nesting hierarchy via geometric polygon containment,
replacing reliance on Camels_jerarquia.shp's `jerarquia` field — that
field was found to be a constant 0 for all 146 basins in the file
(and all 43 in Camels_jerarquia_glaciar_RGI.shp), including basins
that are clearly nested (e.g. Rio Maipo En El Manzano is 100%
contained within Rio Maipo En Cabimbao, yet both are labeled 0).
Source ArcGIS metadata confirms the field was likely never populated
with real values, rather than corrupted downstream.

This logic was originally developed in building_hucs_nested_basins.ipynb
(Cells 2-3) and is extracted here so it has one canonical implementation,
usable by that notebook, 02_glacier_to_basin_script.ipynb, and any
future analysis that needs true basin nesting structure.

Core method: for two basins A (smaller) and B (larger), A is considered
"contained in" B if the overlap between A and B covers more than
CONTAINMENT_THRESHOLD (default 90%) of A's own area. Depth 0 = a basin
that is not contained in any other basin in the candidate set (i.e. a
true top-level/outlet basin, analogous to the old jerarquia=0 meaning
"main basin" — except this is actually verified geometrically).
"""

import numpy as np
import pandas as pd

CONTAINMENT_THRESHOLD = 0.9  # fraction of the smaller basin's area that
                              # must overlap the larger one to count as nested


def build_containment_maps(bounds_utm, candidate_ids=None,
                            containment_threshold=CONTAINMENT_THRESHOLD):
    """
    Compute pairwise containment among basins in a GeoDataFrame.

    bounds_utm: GeoDataFrame of basin polygons, already reprojected to a
                projected CRS (e.g. UTM) so .area is in real units (m^2).
                Must have a 'gauge_id' column and valid geometry.
    candidate_ids: optional iterable of gauge_ids to restrict the O(n^2)
                   containment check to (e.g. only glacierized basins).
                   If None, checks all basins in bounds_utm.

    Returns (contained_map, container_map):
      contained_map[gid] -> list of gauge_ids that gid CONTAINS
                             (i.e. gid is the larger/parent basin)
      container_map[gid] -> list of gauge_ids that CONTAIN gid
                             (i.e. gid is the smaller/child basin)
    """
    ids   = bounds_utm['gauge_id'].values
    geoms = bounds_utm.geometry.values
    areas = bounds_utm.geometry.area.values

    if candidate_ids is not None:
        candidate_set = set(candidate_ids)
        idx_range = [i for i, gid in enumerate(ids) if gid in candidate_set]
    else:
        idx_range = list(range(len(ids)))

    contained_map = {gid: [] for gid in ids}
    for i in idx_range:
        # i is the candidate PARENT (larger basin); j ranges over
        # candidate CHILDREN (smaller basins) that i might contain.
        contained_ids = []
        for j in idx_range:
            if i == j or areas[i] <= areas[j]:
                continue
            overlap = geoms[i].intersection(geoms[j]).area
            # Fraction of the SMALLER basin's (j's) area covered by the
            # overlap — this is what determines whether j is nested
            # inside i, not the other way around.
            if areas[j] > 0 and overlap / areas[j] > containment_threshold:
                contained_ids.append(ids[j])
        contained_map[ids[i]] = contained_ids

    container_map = {gid: [] for gid in ids}
    for child_id, parent_ids in contained_map.items():
        for parent_id in parent_ids:
            container_map.setdefault(parent_id, [])
            container_map[parent_id].append(child_id)

    return contained_map, container_map


def get_immediate_parent(gid, container_map, area_by_id):
    """
    Smallest basin that still contains gid (the closest/immediate parent
    in the nesting chain), or None if gid is not contained in anything.

    container_map: from build_containment_maps — container_map[gid] is
                   the list of gauge_ids that CONTAIN gid.
                   NOTE: despite the name, in build_containment_maps'
                   output this is actually stored the other way — see
                   get_full_chain below for the correct usage pattern.
    area_by_id: dict mapping gauge_id -> area (for picking the smallest
                valid container when there are multiple).
    """
    containers = container_map.get(gid, [])
    if not containers:
        return None
    containers_with_area = [(cid, area_by_id[cid]) for cid in containers
                             if cid in area_by_id]
    if not containers_with_area:
        return None
    containers_with_area.sort(key=lambda x: x[1])
    return containers_with_area[0][0]


def get_full_chain(gid, container_map, area_by_id):
    """
    Full chain from gid up to its top-level (largest) containing basin.
    chain[0] = gid itself, chain[-1] = the major/outlet basin.
    """
    chain = [gid]
    current = gid
    seen = {gid}
    while True:
        parent = get_immediate_parent(current, container_map, area_by_id)
        if parent is None or parent in seen:
            break
        chain.append(parent)
        seen.add(parent)
        current = parent
    return chain


def compute_basin_hierarchy(bounds, candidate_ids=None,
                             containment_threshold=CONTAINMENT_THRESHOLD,
                             utm_epsg=32719):
    """
    Full pipeline: reproject, build containment maps, compute depth/
    immediate_parent/major_basin for every candidate basin.

    bounds: GeoDataFrame of basin polygons in any CRS, with 'gauge_id',
            'gauge_name', and (ideally) 'area_km2' columns.
    candidate_ids: optional iterable of gauge_ids to compute hierarchy
                   for (e.g. only glacierized basins). If None, computes
                   for every basin in `bounds`.
    utm_epsg: projected CRS to reproject into for accurate area/overlap
              math. Default 32719 (UTM 19S, appropriate for Chile).

    Returns a DataFrame with columns: gauge_id, gauge_name, area_km2,
    depth, immediate_parent, major_basin_id, major_basin_name.
    depth == 0 means the basin is NOT nested inside anything else in
    the candidate set — i.e. it is a true top-level/outlet basin.
    """
    bounds_utm = bounds.to_crs(epsg=utm_epsg).copy()
    bounds_utm['gauge_id'] = bounds_utm['gauge_id'].astype(str)

    ids   = bounds_utm['gauge_id'].values
    names = (bounds_utm['gauge_name'].values
             if 'gauge_name' in bounds_utm.columns else ids)
    area_by_id = dict(zip(ids, bounds_utm.geometry.area.values))

    if candidate_ids is not None:
        candidate_ids = [str(g) for g in candidate_ids]

    contained_map, container_map = build_containment_maps(
        bounds_utm, candidate_ids=candidate_ids,
        containment_threshold=containment_threshold)

    target_ids = candidate_ids if candidate_ids is not None else list(ids)

    basin_depth = {}
    basin_immediate_parent = {}
    basin_major_basin = {}
    for gid in target_ids:
        chain = get_full_chain(gid, container_map, area_by_id)
        basin_depth[gid]            = len(chain) - 1
        basin_immediate_parent[gid] = chain[1] if len(chain) > 1 else None
        basin_major_basin[gid]      = chain[-1]

    name_by_id = dict(zip(ids, names))
    area_km2_by_id = (dict(zip(bounds_utm['gauge_id'],
                                bounds['area_km2'].values))
                       if 'area_km2' in bounds.columns else area_by_id)

    df_hierarchy = pd.DataFrame({
        'gauge_id': list(basin_depth.keys()),
        'depth':    list(basin_depth.values()),
    })
    df_hierarchy['gauge_name'] = df_hierarchy['gauge_id'].map(name_by_id)
    df_hierarchy['area_km2']   = df_hierarchy['gauge_id'].map(area_km2_by_id)
    df_hierarchy['immediate_parent'] = df_hierarchy['gauge_id'].map(
        basin_immediate_parent)
    df_hierarchy['major_basin_id'] = df_hierarchy['gauge_id'].map(
        basin_major_basin)
    df_hierarchy['major_basin_name'] = df_hierarchy['major_basin_id'].map(
        name_by_id)

    return df_hierarchy
