UPDATE usgs_gage_data
SET month_day_factor = discharge_cfs / (select est_mean from estimated_flows where est_year = usgs_gage_data.gage_year AND est_month = usgs_gage_data.gage_month and comid = "2665613")
