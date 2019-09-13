import os
from operator import attrgetter
import logging

import fiona

from eflows_optimization import settings
from belleflopt import models

log = logging.getLogger("belleflopt.load")

NO_DOWNSTREAM = ("OCEAN", "MEXICO", "CLOSED_BASIN")


def load_flow_components():
	"""
		We're only doing 5 flow components, so we can load them manually
	:return:
	"""
	models.FlowComponent(name="Fall pulse flow").save()
	models.FlowComponent(name="Wet-season base flow").save()
	models.FlowComponent(name="Peak flow").save()
	models.FlowComponent(name="Spring recession flow").save()
	models.FlowComponent(name="Dry-season base flow").save()


def load_flow_metrics():
	fall_pulse = models.FlowComponent.objects.get(name="Fall pulse flow")
	wet_base = models.FlowComponent.objects.get(name="Wet-season base flow")
	wet_peak = models.FlowComponent.objects.get(name="Peak flow")
	spring_recession = models.FlowComponent.objects.get(name="Spring recession flow")
	dry_base = models.FlowComponent.objects.get(name="Dry-season base flow")

	# Fall Pulse Flow metrics
	models.FlowMetric(characteristic="Magnitude (cfs)",
	                  metric="FA_Mag",
	                  component=fall_pulse,
	                  description="Peak magnitude of fall season pulse event (maximum daily peak flow during event)").save()
	models.FlowMetric(characteristic="Timing (date)",
	                  metric="FA_Tim",
	                  component=fall_pulse,
	                  description="Start date of fall pulse event").save()
	models.FlowMetric(characteristic="Duration (days)",
	                  metric="FA_Dur",
	                  component=fall_pulse,
	                  description="Duration of fall pulse event (# of days start-end)").save()

	# Wet Season Base Flow metrics
	models.FlowMetric(characteristic="Magnitude (cfs)",
	                  metric="Wet_BFL_Mag_10^",
	                  component=wet_base,
	                  description="Magnitude of wet season baseflows (10th percentile of daily flows within that season, including peak flow events)").save()
	models.FlowMetric(characteristic="Magnitude (cfs)",
	                  metric="Wet_BFL_Mag_50^",
	                  component=wet_base,
	                  description="Magnitude of wet season baseflows (50th percentile of daily flows within that season, including peak flow events)").save()
	models.FlowMetric(characteristic="Timing (date)",
	                  metric="Wet_Tim",
	                  component=wet_base,
	                  description="Start date of wet season").save()
	models.FlowMetric(characteristic="Duration (days)",
	                  metric="Wet_BFL_Dur^",
	                  component=wet_base,
	                  description="Wet season baseflow duration (# of days from start of wet season to start of spring season)").save()

	#  Wet Season Peak Flow metrics
	models.FlowMetric(characteristic="Magnitude (cfs)",
	                  metric="Peak_10",
	                  component=wet_peak,
	                  description="Peak-flow magnitude (10% exeedance values of annual peak flow --> 2, 5, and 10 year recurrence intervals)").save()
	models.FlowMetric(characteristic="Magnitude (cfs)",
	                  metric="Peak_20",
	                  component=wet_peak,
	                  description="Peak-flow magnitude (20% exeedance values of annual peak flow --> 2, 5, and 10 year recurrence intervals)").save()
	models.FlowMetric(characteristic="Magnitude (cfs)",
	                  metric="Peak_50",
	                  component=wet_peak,
	                  description="Peak-flow magnitude (50% exeedance values of annual peak flow --> 2, 5, and 10 year recurrence intervals)").save()

	models.FlowMetric(characteristic="Timing (date)",
	                  metric="Peak_Dur_10^",
	                  component=wet_peak,
	                  description="Duration of peak flows over wet season (cumulative number of days in which a given peak-flow recurrence interval is exceeded in a year).").save()
	models.FlowMetric(characteristic="Timing (date)",
	                  metric="Peak_Dur_20^",
	                  component=wet_peak,
	                  description="Duration of peak flows over wet season (cumulative number of days in which a given peak-flow recurrence interval is exceeded in a year).").save()
	models.FlowMetric(characteristic="Timing (date)",
	                  metric="Peak_Dur_50^",
	                  component=wet_peak,
	                  description="Duration of peak flows over wet season (cumulative number of days in which a given peak-flow recurrence interval is exceeded in a year).").save()

	models.FlowMetric(characteristic="Duration (days)",
	                  metric="Peak_Fre_10^",
	                  component=wet_peak,
	                  description="Frequency of peak flow events over wet season (number of times in which a given peak-flow recurrence interval is exceeded in a year).").save()
	models.FlowMetric(characteristic="Duration (days)",
	                  metric="Peak_Fre_20^",
	                  component=wet_peak,
	                  description="Frequency of peak flow events over wet season (number of times in which a given peak-flow recurrence interval is exceeded in a year).").save()
	models.FlowMetric(characteristic="Duration (days)",
	                  metric="Peak_Fre_50^",
	                  component=wet_peak,
	                  description="Frequency of peak flow events over wet season (number of times in which a given peak-flow recurrence interval is exceeded in a year).").save()

	# Spring Recession metrics
	models.FlowMetric(characteristic="Magnitude (cfs)",
	                  metric="SP_Mag^",
	                  component=spring_recession,
	                  description="Spring peak magnitude (daily flow on start date of spring-flow period)").save()
	models.FlowMetric(characteristic="Timing (date)",
	                  metric="SP_Tim^",
	                  component=spring_recession,
	                  description="Start date of spring (date)").save()
	models.FlowMetric(characteristic="Duration (days)",
	                  metric="SP_Dur^",
	                  component=spring_recession,
	                  description="Spring flow recession duration (# of days from start of spring to start of summer baseflow period)").save()
	models.FlowMetric(characteristic="Rate of Change %",
	                  metric="SP_ROC",
	                  component=spring_recession,
	                  description="Spring flow recession rate (Percent decrease per day over spring recession period)").save()

	# Dry Season metrics
	models.FlowMetric(characteristic="Magnitude (cfs)",
	                  metric="DS_Mag_50^",
	                  component=dry_base,
	                  description="Base flow magnitude (50th percentile of daily flow within summer season, calculated on an annual basis)").save()
	models.FlowMetric(characteristic="Magnitude (cfs)",
	                  metric="DS_Mag_90^",
	                  component=dry_base,
	                  description="Base flow magnitude (90th percentile of daily flow within summer season, calculated on an annual basis)").save()
	models.FlowMetric(characteristic="Timing (date)",
	                  metric="DS_Tim^",
	                  component=dry_base,
	                  description="Summer timing (start date of summer)").save()
	models.FlowMetric(characteristic="Duration (days)",
	                  metric="DS_Dur_WS^",
	                  component=dry_base,
	                  description="Summer flow duration (# of days from start of summer to start of wet season)").save()


def load_flow_metric_data(path):
	# load csv

	# we could make it load the NHDSegment if it doesn't exist, but it's probably worth loading from a known dataset beforehand so we can add the downstream information and name

	pass


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

		stream_segment.upstream.add(segment)  # add the upstream huc

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

	# add the immediate networking
	log.info("Building Segment Network")
	for segment in models.StreamSegment.objects.all():
		try:
			downstream = models.StreamSegment.objects.get(upstream_node_id=segment.downstream_node_id)  # get the segment whose upstream node matches the downstream node of this segment
		except models.StreamSegment.MultipleObjectsReturned:  # if we have a split in the river, we get multiple objects back
			# let's figure out which one is more important
			downstream_segments = models.StreamSegment.objects.filter(upstream_node_id=segment.downstream_node_id)
			downstream = max(downstream_segments, key=attrgetter("routed_upstream_area"))  # get the item with the highest routed flow from this segment as the downstream segment

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
