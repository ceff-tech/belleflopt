import sqlite3

years = range(2000, 2016)
months = range(1, 13)

connection = sqlite3.connect(r"C:\Users\dsx\Dropbox\Code\belleflopt\data\navarro\navarro_data.sqlite")
cursor = connection.cursor()

cursor.execute("delete from estimated_daily")  # clear the table first

statement = """INSERT INTO estimated_daily
				select flow.comid as comid, usgs.gage_year as est_year, usgs.gage_month as est_month,
					usgs.gage_day as est_day, 0 as day_of_water_year, flow.est_mean as raw_value, (flow.est_mean * usgs.month_day_factor) as estimated_value,
					usgs.month_day_factor as day_month_factor
				FROM usgs_gage_data as usgs
				CROSS JOIN estimated_flows as flow
				WHERE usgs.gage_year = ? AND usgs.gage_month = ? AND flow.est_year = ? AND flow.est_month = ?
		"""

for year in years:
	print(year)
	for month in months:  # the order of the parameters below matters because it uses order and not names for insertion!
		print("  {}".format(month))
		cursor.execute(statement, (year, month, year, month))
print(cursor.fetchone())

connection.commit()
connection.close()