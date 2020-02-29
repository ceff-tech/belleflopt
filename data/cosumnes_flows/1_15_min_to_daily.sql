INSERT INTO michigan_bar_daily
	SELECT full_date as est_date, avg(Discharge_CFS) as est_mean from MichiganBar15min group by full_date