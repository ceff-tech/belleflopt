"""
	Would often put something like this in tests, but here just want to get some reporting
	without the traditional testing format
"""

import fiona
import csv
import os

def get_all_US_comids(seamless_geodatabase_location=r"C:\Users\dsx\Projects\Data\NHDPlusV21_NationalData_Seamless_Geodatabase_Lower48_07\NHDPlusNationalData\NHDPlusV21_National_Seamless_Flattened_Lower48.gdb"):
	"""
		returns a list of all comids in the US
	:param seamless_geodatabase_location: the path to the seamless geodatabase - Network and NonNetwork COMIDs will be loaded
	:return: list of COMIDs
	"""

	comids = {}  # could preallocate, but whatever
	print("Loading Network COMIDs")
	with fiona.open(seamless_geodatabase_location, driver="OpenFileGDB", layer="NHDFlowline_Network") as nhd_data:
		for row in nhd_data:
			comids[row["properties"]["COMID"]] = 1
	print("Loading NonNetworked COMIDs")
	with fiona.open(seamless_geodatabase_location, driver="OpenFileGDB", layer="NHDFlowline_NonNetwork") as nhd_data:
		for row in nhd_data:
			comids[row["properties"]["COMID"]] = 1

	return comids


def get_model_comids(csv_filepath=r"C:\Users\dsx\Box\CA Flow Model V2\SupplementalMetaData\California_COMIDs.csv"):
	comids = {}

	with open(csv_filepath, 'r') as csv_file:
		reader = csv.DictReader(csv_file)

		for row in reader:
			comids[row["COMID"]] = 1

	return comids


def check_comids(test_csv, source_data_func=get_all_US_comids):
	"""
		Checks that all comids in test_csv exist in the US NHDPlusv2 Seamless dataset
	:param test_csv:
	:param source_data_func: a function that returns a dictionary of COMIDs that are assumed
						to be comprehensive and authoritative. The dictionary
						should be keyed by COMID with any value. COMIDs in test_csv that
						aren't in the dictionary keys will be assumed wrong
	:return:
	"""

	comids = source_data_func()

	missing_comids = []
	with open(test_csv, 'r') as csv_file:
		reader = csv.DictReader(csv_file)

		i = 0
		for row in reader:
			i += 1
			if row["COMID"] not in comids:
				missing_comids.append(row["COMID"])

			if i % 20000 == 0:
				print(i)

		print("## MISSING ##")
		missing = list(set(missing_comids))  # dedupe and print it
		print("{} Missing COMIDs".format(len(missing)))
		test_csv_folder = os.path.split(test_csv)[0]
		with open(os.path.join(test_csv_folder, "missing_comids.csv"), 'w') as output_file:
			for comid in missing:  # printing 1 by 1 because they were getting cut off otherwise
				output_file.write(comid)
				output_file.write("\n")


