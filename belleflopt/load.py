from belleflopt import models


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

	# for each row, check if the

	pass