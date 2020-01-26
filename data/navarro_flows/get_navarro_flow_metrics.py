"""
This script dumps new flow metrics files filtered to include only the segments in the COMID field of COMID_FILE.
Takes inputs from FLOW_METRIC_INPUT folder and puts outputs of the same name in FLOW_METRIC_OUTPUT (must exist).
"""

import os
import csv

FLOW_METRIC_INPUT = r"C:\Users\dsx\Dropbox\Code\belleflopt\data\ffm_modeling\Data\NHD FFM predictions"
FLOW_METRIC_OUTPUT = r"C:\Users\dsx\Dropbox\Code\belleflopt\data\navarro_flows\flow_metrics"
COMID_FILE = r"C:\Users\dsx\Dropbox\Code\belleflopt\data\navarro_flows\navarro_streams.csv"
COMID_FIELD = "COMID"

metric_data = os.listdir(FLOW_METRIC_INPUT)

# get the COMIDs we care about
basin_comids = []
with open(COMID_FILE, 'r') as filehandle:
	csv_reader = csv.DictReader(filehandle)
	for row in csv_reader:
		basin_comids.append(row[COMID_FIELD])

# extract it for each metric
for metric_filename in metric_data:
	input_path = os.path.join(FLOW_METRIC_INPUT, metric_filename)
	if not os.path.isfile(input_path) or metric_filename == "desktop.ini":
		continue

	print(metric_filename)
	with open(input_path, 'r') as filehandle:
		with open(os.path.join(FLOW_METRIC_OUTPUT, metric_filename), 'w', newline="\n") as output_filehandle:
			csv_reader = csv.DictReader(filehandle)
			csv_writer = csv.DictWriter(output_filehandle, fieldnames=["FFM","COMID","p10","p25","p50","p75","p90","source"])
			csv_writer.writeheader()
			for row in csv_reader:
				if row[COMID_FIELD] in basin_comids:
					csv_writer.writerow(row)