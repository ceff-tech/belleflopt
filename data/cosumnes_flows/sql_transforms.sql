
-- Create the 15 minute table
CREATE TABLE MichiganBar15min (
	full_date TEXT,
	Discharge_CFS NUMERIC
);

-- NOW NEED TO LOAD THE DATA MANUALLY INTO THIS TABLE

CREATE TABLE michigan_bar_daily (
	est_date TEXT,
	est_mean NUMERIC,
	gage_year INTEGER,
	gage_month INTEGER,
	gage_day INTEGER,
	month_day_factor REAL
);


-- Clear the table out in case we rerun this after creation
delete from michigan_bar_daily;

-- Get the daily mean into this table
-- Need the NULLs so that the extra fields get populated
INSERT
	INTO
	michigan_bar_daily
SELECT
	full_date as est_date,
	avg(Discharge_CFS) as est_mean,
	NULL,
	NULL,
	NULL,
	NULL
from
	MichiganBar15min
group by
	full_date;

-- A null record snuck in
delete from michigan_bar_daily where est_mean is NULL;

-- Update the year
update
	michigan_bar_daily set
	gage_year = 
		substr(est_date,
		0,
		5);

-- Update month
update
	michigan_bar_daily set
	gage_month = 
		substr(est_date,
		6,
		2);
		
-- Update day
update
	michigan_bar_daily set
	gage_day = 
		substr(est_date,
		9,
		2);
		
-- Get conversion factor - estimated_flows is from unimpaired flows DB and michigan_bar_daily is daily gage data
UPDATE
	michigan_bar_daily as mbd
SET
	month_day_factor = est_mean / (
	select
		ef.est_mean
	from
		estimated_flows as ef
	where
		ef.est_year = mbd.gage_year
		AND ef.est_month = mbd.gage_month
		and ef.comid = "20192498"
	);
	
-- Confirm it looks good
select
	mbd.gage_month,
	mbd.gage_year,
	min(mbd.month_day_factor),
	avg(mbd.month_day_factor),
	max(mbd.month_day_factor)
from
	michigan_bar_daily as mbd
group by
	mbd.gage_year,
	mbd.gage_month;
	
-- now create the daily flows table for all segments
CREATE TABLE estimated_daily_all (
	comid TEXT NOT NULL,
	est_year INTEGER NOT NULL,
	est_month INTEGER NOT NULL,
	est_day INTEGER NOT NULL,
	day_of_water_year INTEGER,
	raw_value REAL,
	estimated_value INTEGER
	day_month_factor REAL,
	comid_int INTEGER,
	full_date TEXT
);

CREATE INDEX estimated_daily_comid_IDX ON estimated_daily_all (comid);
CREATE INDEX estimated_daily_est_year_IDX ON estimated_daily_all (est_year,est_month);


-- now configure and run the Python cross join script