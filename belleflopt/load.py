import os
from operator import attrgetter
import logging
import csv
import sqlite3
import re

import django
import fiona
import arrow

from eflows_optimization import settings
from belleflopt import models, support

log = logging.getLogger("belleflopt.load")


def load_fresh(import_nhd=True, clear_flow_data=True):
	"""
		Loads everything in the proper order for a fresh database
		:param import_nhd: when True, loads NHD data. It will not remove existing data first - it assumes you
							have an empty database or have removed the data manually
		:param clear_flow_data: when True, deletes all flow components (defs), metrics (defs),
		                    segment components, and component descriptors before loading flow data. When False,
		                    will load those on top of any existing data for those models.
	:return:
	"""
	# load the NHD, then traverse the network to add downstream data to the items
	if import_nhd:
		load_nhd()

	if clear_flow_data:
		log.info("Clearing flow data")
		models.SegmentComponentDescriptor.objects.all().delete()
		models.SegmentComponent.objects.all().delete()
		models.FlowMetric.objects.all().delete()
		models.FlowComponent.objects.all().delete()

	# now load flow components and metrics, as well as data for it
	log.info("Loading flow data")
	load_flow_components()
	load_flow_metrics()
	log.info("Creating Segment Components")
	create_all_segment_components()
	log.info("Loading Flow Metric Data")
	load_all_flow_metric_data()

	# build segment_component values
	log.info("Building Components")
	build_segment_components()

	load_flows(clear_existing=clear_flow_data)
	log.info("Complete. Don't forget to load species data for your model")


def load_flow_components():
	"""
		We're only doing 5 flow components, so we can load them manually
	:return:
	"""
	models.FlowComponent(name="Fall pulse flow", ceff_id="FA").save()
	models.FlowComponent(name="Wet-season base flow", ceff_id="Wet_BFL").save()
	models.FlowComponent(name="Peak flow", ceff_id="Peak").save()
	models.FlowComponent(name="Spring recession flow", ceff_id="SP").save()
	models.FlowComponent(name="Dry-season base flow", ceff_id="DS").save()


def load_flow_metrics():
	fall_pulse = models.FlowComponent.objects.get(name="Fall pulse flow")
	wet_base = models.FlowComponent.objects.get(name="Wet-season base flow")
	wet_peak = models.FlowComponent.objects.get(name="Peak flow")
	spring_recession = models.FlowComponent.objects.get(name="Spring recession flow")
	dry_base = models.FlowComponent.objects.get(name="Dry-season base flow")

	# Fall Pulse Flow metrics
	fall_pulse.metrics.create(characteristic="Magnitude (cfs)",
	                  metric="FA_Mag",
	                  description="Peak magnitude of fall season pulse event (maximum daily peak flow during event)")
	fall_pulse.metrics.create(characteristic="Timing (date)",
	                  metric="FA_Tim",
	                  description="Start date of fall pulse event")
	fall_pulse.metrics.create(characteristic="Duration (days)",
	                  metric="FA_Dur",
	                  description="Duration of fall pulse event (# of days start-end)")

	# Wet Season Base Flow metrics
	wet_base.metrics.create(characteristic="Magnitude (cfs)",
	                  metric="Wet_BFL_Mag_10",
	                  description="Magnitude of wet season baseflows (10th percentile of daily flows within that season, including peak flow events)")
	wet_base.metrics.create(characteristic="Magnitude (cfs)",
	                  metric="Wet_BFL_Mag_50",
	                  description="Magnitude of wet season baseflows (50th percentile of daily flows within that season, including peak flow events)")

	# these two metrics have multiple components
	wet_timing = models.FlowMetric(characteristic="Timing (date)",
	                  metric="Wet_Tim",
	                  description="Start date of wet season")
	wet_timing.save()
	wet_timing.components.add(wet_base, wet_peak)
	wet_timing.save()
	wet_duration = models.FlowMetric(characteristic="Duration (days)",
	                  metric="Wet_BFL_Dur",
	                  description="Wet season baseflow duration (# of days from start of wet season to start of spring season)")
	wet_duration.save()
	wet_duration.components.add(wet_base, wet_peak)
	wet_duration.save()

	#  Wet Season Peak Flow metrics
	wet_peak.metrics.create(characteristic="Magnitude (cfs)",
	                  metric="Peak_10",
	                  description="Peak-flow magnitude (10 year/10% exeedance values of annual peak flow --> 2, 5, and 10 year recurrence intervals)")
	wet_peak.metrics.create(characteristic="Magnitude (cfs)",
	                  metric="Peak_5",
	                  description="Peak-flow magnitude (5 year/20% exeedance values of annual peak flow --> 2, 5, and 10 year recurrence intervals)")
	wet_peak.metrics.create(characteristic="Magnitude (cfs)",
	                  metric="Peak_2",
	                  description="Peak-flow magnitude (2 year/50% exeedance values of annual peak flow --> 2, 5, and 10 year recurrence intervals)")

	wet_peak.metrics.create(characteristic="Timing (date)",
	                  metric="Peak_Dur_10",
	                  description="Duration of peak flows over wet season for 10% exceedence/10 year recurrence (cumulative number of days in which a given peak-flow recurrence interval is exceeded in a year).")
	wet_peak.metrics.create(characteristic="Timing (date)",
	                  metric="Peak_Dur_5",
	                  description="Duration of peak flows over wet season 20% exceedence/5 year recurrence (cumulative number of days in which a given peak-flow recurrence interval is exceeded in a year).")
	wet_peak.metrics.create(characteristic="Timing (date)",
	                  metric="Peak_Dur_2",
	                  description="Duration of peak flows over wet season 50% exceedence/2 year recurrence (cumulative number of days in which a given peak-flow recurrence interval is exceeded in a year).")

	wet_peak.metrics.create(characteristic="Duration (days)",
	                  metric="Peak_Fre_10",
	                  description="Frequency of peak flow events over wet season (number of times in which a given peak-flow recurrence interval is exceeded in a year).")
	wet_peak.metrics.create(characteristic="Duration (days)",
	                  metric="Peak_Fre_5",
	                  description="Frequency of peak flow events over wet season (number of times in which a given peak-flow recurrence interval is exceeded in a year).")
	wet_peak.metrics.create(characteristic="Duration (days)",
	                  metric="Peak_Fre_2",
	                  description="Frequency of peak flow events over wet season (number of times in which a given peak-flow recurrence interval is exceeded in a year).")

	# Spring Recession metrics
	spring_recession.metrics.create(characteristic="Magnitude (cfs)",
	                  metric="SP_Mag",
	                  description="Spring peak magnitude (daily flow on start date of spring-flow period)")
	spring_recession.metrics.create(characteristic="Timing (date)",
	                  metric="SP_Tim",
	                  description="Start date of spring (date)")
	spring_recession.metrics.create(characteristic="Duration (days)",
	                  metric="SP_Dur",
	                  description="Spring flow recession duration (# of days from start of spring to start of summer baseflow period)")
	spring_recession.metrics.create(characteristic="Rate of Change %",
	                  metric="SP_ROC",
	                  description="Spring flow recession rate (Percent decrease per day over spring recession period)")

	# Dry Season metrics
	dry_base.metrics.create(characteristic="Magnitude (cfs)",
	                  metric="DS_Mag_50",
	                  description="Base flow magnitude (50th percentile of daily flow within summer season, calculated on an annual basis)")
	dry_base.metrics.create(characteristic="Magnitude (cfs)",
	                  metric="DS_Mag_90",
	                  description="Base flow magnitude (90th percentile of daily flow within summer season, calculated on an annual basis)")
	dry_base.metrics.create(characteristic="Timing (date)",
	                  metric="DS_Tim",
	                  description="Summer timing (start date of summer)")
	dry_base.metrics.create(characteristic="Duration (days)",
	                  metric="DS_Dur_WS",
	                  description="Summer flow duration (# of days from start of summer to start of wet season)")


def _get_upstream(stream_segment, force=False):
	if stream_segment.upstream.count() > 0 and not force:
		return  # if this function is called when it already has upstream hucs defined, it's already complete - return immediately

	upstream = models.StreamSegment.objects.filter(downstream_node_id=stream_segment.upstream_node_id)  # get all the immediately upstream segments of the current segment
	for segment in upstream:  # for each upstream huc, find *its* upstream hucs and add them here too
		_get_upstream(segment, force=force)  # this needs to run for all the upstream hucs first
		segment.refresh_from_db()  # make sure it correctly gets the new info we just loaded for it in _get_upstream

		if segment.upstream.count() > 0:  # if the upstream segments has upstream segments of its own
			for upstream_segment in segment.upstream.all():
				if upstream_segment.com_id == segment.com_id or upstream_segment.com_id == stream_segment.com_id or (stream_segment.downstream is not None and upstream_segment.com_id == stream_segment.downstream.com_id):
					# seems like this checks that we're not creating loops? Not totally positive.
					continue

				# add all the items upstream as upstream of the current segment
				stream_segment.upstream.add(upstream_segment)
	# now we can fill in the current huc with the upstream hucs filled
	# ON DEBUG - confirm that these instances will pick up upstream changes in recursive function

		stream_segment.upstream.add(segment)  # add the upstream segment

	stream_segment.save()


def load_nhd(gdb=os.path.join(settings.BASE_DIR, "data", "NHDPlusV2", "NHDPlusV2.gdb")):
	with fiona.open(gdb, driver="OpenFileGDB", layer="NHDFlowline_Network") as nhd_data:
		log.info("Loading Networked NHD Stream Segments")

		for row in nhd_data:
			properties = row["properties"]
			try:
				models.StreamSegment.objects.get(com_id=properties["COMID"])
				continue  # if it exists, don't load it again
			except models.StreamSegment.DoesNotExist:
				pass

			segment = models.StreamSegment()
			segment.com_id = properties["COMID"]
			segment.name = properties["GNIS_NAME"]
			segment.ftype = properties["FTYPE"] if properties["FTYPE"] not in (None, "", " ") else None
			segment.strahler_order = properties["StreamOrde"] if properties["StreamOrde"] > 0 else None
			segment.total_upstream_area = properties["TotDASqKM"] if properties["TotDASqKM"] >= 0 else None
			segment.routed_upstream_area = properties["DivDASqKM"] if properties["DivDASqKM"] >= 0 else None
			segment.upstream_node_id = round(properties["FromNode"])  # using round instead of math.floor because of the case where it approximates a value like 2 as 1.99999999999 or something. Most will be 0
			segment.downstream_node_id = round(properties["ToNode"])  # using round instead of math.floor because of the case where it approximates a value like 2 as 1.99999999999 or something. Most will be 0
			segment.save()  # we need to save before we can set the downstreams

	load_downstream_data()


def load_downstream_data():
	# add the immediate networking
	log.info("Building Segment Network")
	for segment in models.StreamSegment.objects.all():
		try:
			downstream = models.StreamSegment.objects.get(upstream_node_id=segment.downstream_node_id)  # get the segment whose upstream node matches the downstream node of this segment
		except models.StreamSegment.MultipleObjectsReturned:  # if we have a split in the river, we get multiple objects back
			# let's figure out which one is more important
			downstream_segments = models.StreamSegment.objects.filter(upstream_node_id=segment.downstream_node_id)
			downstream = max(downstream_segments, key=attrgetter("routed_upstream_area"))  # get the item with the highest routed flow from this segment as the downstream segment
		except models.StreamSegment.DoesNotExist:
			log.warning("NHD Segment with upstream node id {} does not exist to attach to {} as downstream. Skipping".format(segment.downstream_node_id, str(segment)))
			continue

		segment.downstream = downstream
		segment.save()

	_build_network()


def _build_network(force=False, starting_segment=None):
	"""
		Force runs *much* slower, but forces a full rebuild of the network
	:param force:
	:return:
	"""
	log.info("Building NHD segment network")
	if starting_segment:
		segment = models.StreamSegment.objects.get(com_id=starting_segment)
		_get_upstream(segment, force=force)  # run it for everything to make sure it's complete. force makes it redo the calculation even if it already has upstream definitions
	else:
		# if no starting segment is provided, then run it for them all - super slow, but ensures it's done correctly. Could be optimized heavily
		for segment in models.StreamSegment.objects.all():
			_get_upstream(segment, force=force)


def load_all_flow_metric_data(folder=settings.LOAD_FFM_FOLDER, ffms=settings.LOAD_FFMS, suffix=settings.LOAD_FFM_SUFFIX):
	"""
		Loads all flow metric data configured for loading in settings

	:param folder:
	:param ffms: Function Flow Metric names. Used in conjunction with the suffix to find filenames in `folder` to load
	:param suffix:
	:return:
	"""
	for ffm in ffms:
		log.info("Loading {}".format(ffm))
		load_single_flow_metric_data(os.path.join(folder, "{}{}".format(ffm, suffix)))


class DataLoadingError(BaseException):
	"""
		Just helps us tease out base exceptions from the ones we want to skip. Only use for cases
		where you want to signal to a calling function that it's OK to skip it
	"""
	pass


def _validate_records(csv_path):
	"""
		Doesn't yet do any validation, just does min and max (and I think it does them wrong?)
	:param csv_path:
	:return:
	"""
	all_numbers = []
	with open(csv_path, 'r') as csv_filehandle:
		csv_data = csv.reader(csv_filehandle)
		header = None
		for record in csv_data:
			if not header:
				header = record
				continue
			all_numbers.extend(record[2:7])

	log.debug(min(all_numbers))
	log.debug(max(all_numbers))


def load_single_flow_metric_data(csv_path, com_id_field="COM_ID"):
	"""
		Given a CSV of modeled stream segment flow metric percentiles, loads this data. Does NOT fill in the actual
		component values for the segments based on the loaded data though.
	:param csv_path:
	:return:
	"""
	# _validate_records(csv_path)  - was trying to track down an error, but it was elsewhere

	with open(csv_path, 'r') as csv_filehandle:
		csv_data = csv.DictReader(csv_filehandle)

		log.info("Loading Flow Metric (SegmentComponent) Descriptors")
		descriptors = []
		for record in csv_data:
			try:
				descriptors.append(_load_segment_data(record))
			except DataLoadingError:
				log.debug("DataLoadingError triggered. Rolling through as intended")
				pass  # DataLoadingError is something we created to signal to the caller that we can roll through.

	# save everything we created, but efficiently
	try:
		log.info("Running DB Query to Create Flow Metric (SegmentComponent) Descriptors")
		models.SegmentComponentDescriptor.objects.bulk_create(descriptors)
	except django.db.utils.IntegrityError:
		# at least one table (Peak_20) fails because it supposedly has a duplicate SegmentComponent+Metric.
		# try to insert normally, and if it fails, report and tell the user, then insert it anyway and ignore the problem
		log.warning("Inserting values for {} while ignoring rows that fail DB constraints. Tried to insert while "
		            "obeying constraints, but DB reported constraint failure - some data may be missing, and you"
		            "should probably track down the source of a (likely) duplicate row to know *what's* missing."
		            " Right now, I don't know, and can't tell you. Sorry.".format(os.path.split(csv_path)[1]))
		models.SegmentComponentDescriptor.objects.bulk_create(descriptors, ignore_conflicts=True)

	# now create the associations - we do it this way because the descriptors need to be created and have IDs in order
	# to be able to be associated with
	log.info("Attaching SegmentComponentDescriptors to SegmentComponents")
	create_associations = []
	descriptors = models.SegmentComponentDescriptor.objects.all()

	for descriptor in descriptors:
		# through is the table generated by django to link m2m between tag and photo
		if descriptor.associated_components_holding_dont_use is not None:
			component_ids = descriptor.associated_components_holding_dont_use.split(",")
		else:
			component_ids = []

		for component_id in component_ids:
			descriptor_component_association = models.SegmentComponentDescriptor.flow_components.through(
				segmentcomponentdescriptor_id=descriptor.id,
				segmentcomponent_id=int(component_id)
			)
			create_associations.append(descriptor_component_association)
			descriptor.associated_components_holding_dont_use = None

	log.info("Executing Query to attach SegmentComponentDescriptors to SegmentComponents")
	models.SegmentComponentDescriptor.flow_components.through.objects.bulk_create(create_associations)

	log.info("Nulling temporary storage field")
	models.SegmentComponentDescriptor.objects.bulk_update(descriptors, fields=['associated_components_holding_dont_use'])  # runs the nulling operation on the holding field

	clean_segment_component_descriptors()


def clean_segment_component_descriptors():
	"""
		The new method of Many to Many relationship for SegmentComponentDescriptors to SegmentComponents means that we
		can't enforce the unique constraint on metric/component/segment combinations. We don't expect duplicates except
		with bad input data (which we've gotten). We might want to make this function "louder" in logging.
		This processes all existing
		SegmentComponentDescriptors and removes any that have duplicate metric/component/segment combinations, keeping
		the first one it finds. This is probably going to be slow.
	:return:
	"""
	log.debug("Enforcing no duplicates for SegmentComponentDescriptors")
	unique = {}
	seg_comp_descs = models.SegmentComponentDescriptor.objects.all()
	for scd in seg_comp_descs:
		for segment_component in scd.flow_components.all():
			key = "{}.{}.{}".format(scd.flow_metric.pk, segment_component.stream_segment.pk, segment_component.component.pk)
			if key in unique:
				scd.delete()
			else:
				unique[key] = True


def create_all_segment_components():
	"""
		Precreates all possible segment components - allows us to bulk create them instead of doing it on demand.
		The workflow where these were created individually was painfully slow and might have taken even a full day
		to insert
	:return:
	"""
	segment_components = []

	flow_components = list(models.FlowComponent.objects.all())  # just get it once and keep using the same items
																# so they don't go out of scope and we don't have to
																# go back to Django for them

	# a nested for loop is actually better than the alternative - we were creating them as needed before
	# and couldn't bulk insert, and the DB transactions were killing performance
	i = 0
	for segment in models.StreamSegment.objects.all():
		i+=1
		if i % 1000 == 0:
			log.debug("Associated components with {} segments".format(i))
		for component in flow_components:
			segment_components.append(models.SegmentComponent(stream_segment=segment, component=component))

	models.SegmentComponent.objects.bulk_create(segment_components)


def _load_segment_data(record, name_field="FFM", create=True):
	"""
		Loads the data for a single segment based on a dictionary from a CSV dictreader
	:param record:
	:return:
	"""
	# look up flow metric - then look up its component and see if a segmentcomponent exists for this item
	if record[name_field] is None or record[name_field] == "":
		raise DataLoadingError("No value for name field in record. Skipping")

	try:
		metric = models.FlowMetric.objects.get(metric=record[name_field])
	except models.FlowMetric.DoesNotExist:
		raise ValueError("No metric loaded for [{}]".format(record[name_field]))

	try:
		segment = models.StreamSegment.objects.get(com_id=record["COMID"])
	except models.StreamSegment.DoesNotExist:
		log.warning("Couldn't load data for COMID {}. Segment not loaded in database.".format(record["COMID"]))
		raise DataLoadingError("No segment to attach to. Skipping")

	descriptor = models.SegmentComponentDescriptor()
	components = []
	for component in metric.components.all():  # there's a many to many relationship between metrics and components, so make sure to attach all segment components to this metric's data
		try:  # we could probably optimize this out by rolling through once and creating all these
			segment_component = models.SegmentComponent.objects.get(stream_segment=segment, component=component)
		except models.SegmentComponent.DoesNotExist:  # if not, create one, if so, get it
			segment_component = models.SegmentComponent()
			segment_component.stream_segment = segment
			segment_component.component = component
			segment_component.save()

		components.append(str(segment_component.pk))

	descriptor.associated_components_holding_dont_use = ",".join(components)
	# NOTE: We don't attach segment_components here because we'd need to do a save and couldn't do efficient bulk
	# operations. We'll do that in a function that follows this in sequence. This attachment on the line above is
	# meant as an efficient interim operation. See large comment on model itself for reasoning and information about
	# this choice and strategy.

	descriptor.flow_metric = metric
	if "source" in record:
		descriptor.source_type = record["source"]
	if "source2" in record:
		descriptor.source_name = record["source2"]
	if "Notes" in record:
		descriptor.notes = record["Notes"]

	descriptor.pct_10 = record["p10"]
	descriptor.pct_25 = record["p25"]
	descriptor.pct_50 = record["p50"]
	descriptor.pct_75 = record["p75"]
	descriptor.pct_90 = record["p90"]

	# Don't save, we'll use bulk_create to do one big transaction and efficiently run the inserts
	return descriptor


def build_segment_components(simple_test=True):
	"""
		Takes all of the segment components and generates their actual bounding values based on their flow metrics
		:param simple_test: When True, checks to see if a specific item built correctly
	:return:
	"""

	# we could speed this up if build() didn't save itself, and then
	# we used the components here in a mass update. Might still be pretty slow though
	# because we're iterating through everything.
	for segment_component in models.SegmentComponent.objects.all():
		segment_component.build()

	if simple_test:
		# check that things loaded
		DS = models.FlowComponent.objects.get(ceff_id="DS")
		items = models.SegmentComponent.objects.filter(component=DS, descriptors__id__gt=0)  # get everything with component descriptors defined
		items[0].build()  # build the first item
		if not (items[0].start_day > -1):  # and make sure it has a valid start day
			log.warning("It's possible an error occurred during building segment components - the first item has no start day, which may indicate a failure of the building pipeline")


def check_missing(filepath=r"C:\Users\dsx\Dropbox\Code\belleflopt\data\ffm_modeling\Data\NHD Attributes\nhd_COMID_classification.csv"):
	"""
		A tool to compare which COMIDs in a spreadsheet are missing from our database
	:param filepath:
	:return:
	"""
	with open(filepath, 'r') as filehandle:
		csv_reader = csv.DictReader(filehandle)
		missing_count = 0
		missing_comids = []
		for row in csv_reader:
			try:
				models.StreamSegment.objects.get(com_id=int(row["COMID"]))
			except models.StreamSegment.DoesNotExist:
				missing_count += 1
				missing_comids.append(row["COMID"])
				log.warning("Missing segment {}. Missing Count: {}".format(int(row["COMID"]), missing_count))

		log.warning("missing IDs: {}".format(str(missing_comids)))


def load_flows(database=os.path.join(settings.BASE_DIR, "data", "navarro_flows", "data_processing", "navarro_data.sqlite"),
				table="estimated_daily",
				comid_field = "comid",
				year_field="est_year",
				month_field="est_month",
				day_field="est_day",
				flow_field="estimated_value",
				water_years=(2010, 2011),
                model_run_name="navarro_thesis",
				clear_existing=True,
                allocate_downstream=True):

	if clear_existing:
		log.info("Deleting existing flow data")
		models.DailyFlow.objects.all().delete()

	db_connection = sqlite3.connect(database)
	cursor = db_connection.cursor()

	# query gets all the flows for a single water year when properly parameterized
	query = """SELECT {}, {}, {}, {}, {}
				FROM {}
				WHERE ({} >= 10 AND {} = ?)
				   OR ({} < 10 AND {} = ?)
	""".format(comid_field, year_field, month_field, day_field, flow_field, table,
	           month_field, year_field, month_field, year_field,)  # note string interpolation - not a web safe query!

	flow_objects = []

	model_run = models.ModelRun.objects.get(name=model_run_name)

	for year in water_years:
		log.info("Loading Water Year {} flows".format(year))
		flows = cursor.execute(query, (year - 1, year))

		log.info("Constructing records")
		for flow in flows:
			flow_objects.append(models.DailyFlow(
				stream_segment=models.StreamSegment.objects.get(com_id=flow[0]),
				model_run=model_run,
				flow_date=arrow.Arrow(flow[1], flow[2], flow[3]).date(),
				water_year=support.water_year(year=flow[1], month=flow[2]),
				water_year_day=support.day_of_water_year(year=flow[1], month=flow[2], day=flow[3]),
				estimated_flow=flow[4]
			))

	log.info("Bulk inserting records")
	models.DailyFlow.objects.bulk_create(flow_objects)

	cursor.close()
	db_connection.close()

	if allocate_downstream:
		model_run.preprocess_flows()

	model_run.update_segments()


def load_species(database=r"C:\Users\dsx\Dropbox\Code\ProbabilisticPISCES\results\results_2019_10_22_base90_decay50.gpkg",
                 table=r"pisces_probabilities_2019_10_22_base90_decay50",
                 comid_field="COMID",
                 model_run=None):

	"""
		Loads species data for all comids in model_run
	:param database:
	:param table:
	:param comid_field:
	:param model_run: Only loads data for these segments
	:return:
	"""

	model_run_comids = [seg.com_id for seg in model_run.segments.all()]

	with sqlite3.Connection(database) as connection:
		connection.row_factory = sqlite3.Row  # we need to do this so we can index by name
		cursor = connection.cursor()
		results = cursor.execute("select * from {}".format(table))

		keys = None
		for row in results:
			if str(row[comid_field]) not in model_run_comids:
				continue  # skip any segments not in this model run

			if keys is None:
				keys = [field for field in row.keys() if re.match("[A-Z]{3}[0-9]{2}", field) is not None]

			segment = models.StreamSegment.objects.get(com_id=row[comid_field])
			for key in keys:
				if row[key] == 0:  # we won't load absent species
					continue

				try:
					species = models.Species.objects.get(pisces_fid=key)
				except models.Species.DoesNotExist:
					species = models.Species(pisces_fid=key, common_name="")  # temporary fix - don't want to load species right now
					species.save()

				models.SegmentPresence(stream_segment=segment,
				                       species=species,
				                       probability=row[key]).save()

	log.info("Caching summed segment species presence probabilities")
	# update the cached species presence values
	for segment in model_run.segments.all():
		segment.calculate_species_presence()
		segment.save()
