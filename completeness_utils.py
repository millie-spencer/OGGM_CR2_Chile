"""
completeness_utils.py

Shared streamflow-gauge daily-completeness criteria (Alexis Caro's method),
used by both the main national pipeline (all_chile_glacier_streamflow_v3.ipynb,
Cell 8) and the grouped-basin pipeline (glacier_to_basin_script.ipynb).

Previously this logic was implemented independently in both notebooks 01 and 02.
Any future change to the completeness criteria (e.g. revisiting the
5-and-5 decade-split rule) should be made HERE ONLY, so both pipelines
stay in sync automatically.

TWO-ZONE RULE:
  North/Central (lat > -38S): >= 5 complete years in 2000-2009
                               AND >= 5 complete years in 2010-2019
  South         (lat <= -38S): >= 10 complete years anywhere in 2000-2019

A year is "complete" if:
  Summer months (Dec-Apr): >= 70% of days non-NaN and Q >= 0
    AND all 5 of Dec, Jan, Feb, Mar, Apr must meet this threshold
  Winter months (May-Nov): >= 50% of days non-NaN and Q >= 0
    AND at least 4 of 7 winter months must meet this threshold

Note: Dec of a year is treated as belonging to the FOLLOWING year's
summer (e.g. Dec 2004 counts toward the 2005 summer season), matching
Southern Hemisphere hydrological convention.
"""

import calendar

LAT_BOUNDARY     = -38.0
SUMMER_MONTHS    = [12, 1, 2, 3, 4]
WINTER_MONTHS    = [5, 6, 7, 8, 9, 10, 11]
SUMMER_THRESHOLD = 0.70
WINTER_THRESHOLD = 0.50


def days_in_month(year, month):
    return calendar.monthrange(year, month)[1]


def month_completeness(q_day, q_day_col, year, month):
    """
    Fraction of days with valid Q in a given year-month.

    q_day: the full daily Q DataFrame (must have 'year' and 'month' columns)
    q_day_col: Series of Q values for one gauge, aligned to q_day's index
    """
    mask = (q_day['year'] == year) & (q_day['month'] == month)
    vals = q_day_col[mask]
    if len(vals) == 0:
        return 0.0
    n_valid = (vals.notna() & (vals >= 0)).sum()
    return n_valid / days_in_month(year, month)


def assess_completeness(q_day, gauge_id, cen_lat):
    """
    Assess whether one gauge passes Alexis's daily-completeness criteria.

    q_day: the full daily Q DataFrame (must have 'year', 'month' columns
           and one column per gauge_id)
    gauge_id: the gauge to assess (must match a column name in q_day)
    cen_lat: the gauge's centroid latitude (determines N/C vs S zone)

    Returns a dict: passes, reason, n_complete, n_pre2010, n_post2010,
    complete_years
    """
    if gauge_id not in q_day.columns:
        return {'passes': False, 'reason': 'no Q column',
                'n_complete': 0, 'n_pre2010': 0, 'n_post2010': 0,
                'complete_years': []}

    col = q_day[gauge_id]

    complete_years = []
    for year in range(2000, 2020):
        # Summer: Dec of PRIOR year + Jan-Apr of this year
        dec_frac = month_completeness(q_day, col, year - 1, 12)
        jan_frac = month_completeness(q_day, col, year, 1)
        feb_frac = month_completeness(q_day, col, year, 2)
        mar_frac = month_completeness(q_day, col, year, 3)
        apr_frac = month_completeness(q_day, col, year, 4)

        summer_fracs = [dec_frac, jan_frac, feb_frac, mar_frac, apr_frac]
        summer_ok    = all(f >= SUMMER_THRESHOLD for f in summer_fracs)

        # Winter: May-Nov, need >= 4 of 7 months above 50% threshold
        winter_fracs = [month_completeness(q_day, col, year, mo)
                        for mo in WINTER_MONTHS]
        winter_ok    = sum(f >= WINTER_THRESHOLD for f in winter_fracs) >= 4

        if summer_ok and winter_ok:
            complete_years.append(year)

    n_pre  = sum(1 for y in complete_years if y <= 2009)
    n_post = sum(1 for y in complete_years if y >= 2010)
    n_tot  = len(complete_years)

    if cen_lat > LAT_BOUNDARY:
        passes = (n_pre >= 5 and n_post >= 5)
        reason = (f'OK (N/C): {n_pre} pre-2010, {n_post} post-2010'
                  if passes else
                  f'FAIL (N/C): {n_pre} pre-2010, {n_post} post-2010')
    else:
        passes = (n_tot >= 10)
        reason = (f'OK (S): {n_tot} complete years'
                  if passes else
                  f'FAIL (S): only {n_tot} complete years')

    return {
        'passes':         passes,
        'reason':         reason,
        'n_complete':     n_tot,
        'n_pre2010':      n_pre,
        'n_post2010':     n_post,
        'complete_years': complete_years,
    }
