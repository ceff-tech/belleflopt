from eflows_optimization import local_settings
from belleflopt import benefit


class BaseFlowComponentBenefitManager(object):
	pass


class SpringRecessionBenefitManager(BaseFlowComponentBenefitManager):
	pass


class SummerBaseFlowBenefitManager(BaseFlowComponentBenefitManager):
	pass


class FallInitiationBenefitManager(BaseFlowComponentBenefitManager):
	pass


class WinterBaseFlowBenefitManager(BaseFlowComponentBenefitManager):
	pass


class WinterPeakFlowBenefitManager(BaseFlowComponentBenefitManager):
	pass

id_manager_map = {
	"Mag_50": SummerBaseFlowBenefitManager,
	"Peak_20": WinterPeakFlowBenefitManager,
}


class BaseFlowComponentBuilder(object):
	pass


class SpringRecessionBuilder(BaseFlowComponentBuilder):
	pass


class SummerBaseFlowBuilder(BaseFlowComponentBuilder):
	def __init__(self, segment_component):
		"""
			This method needs serious testing.

			Gets the full set of q values for magnitude from one flow metric and makes a benefit object using those
			values. For timing, it pulls the start timing from one metric, and the duration from another. Which percentile
			it uses is configured in local_settings
		:param segment_component:
		"""
		self.segment_component = segment_component

		# Get the flow metric values specific to this segment, that match what we need as defined in local_settings
		magnitude_definition = self.segment_component.metrics.get(flow_metric__metric=local_settings.SUMMER_BASEFLOW_MAGNITUDE_METRIC)
		start_timing_definition = self.segment_component.metrics.get(flow_metric__metric=local_settings.SUMMER_BASEFLOW_START_TIMING_METRIC)
		end_duration_definition = self.segment_component.metrics.get(flow_metric__metric=local_settings.SUMMER_BASEFLOW_DURATION_METRIC)
		start_timing_vals = local_settings.SUMMER_BASEFLOW_START_TIMING_VALUES
		duration_vals = local_settings.SUMMER_BASEFLOW_DURATION_VALUES

		self.benefit = benefit.BenefitBox()  # make a benefit box and set the magnitude q values immediately
		self.benefit.flow_item.set_values(magnitude_definition.p10, magnitude_definition.p25, magnitude_definition.p75, magnitude_definition.p90)

		# get the actual start timing values, then calculate the end values using the start timing and duration (as defined by preferences in
		# local_settings), and set the q values based on these looked up values
		p25_start_timing = getattr(start_timing_definition, start_timing_vals[1])
		self.benefit.date_item.set_values(getattr(start_timing_definition, start_timing_vals[0]),
		                                  p25_start_timing,
		                                  p25_start_timing + getattr(end_duration_definition, duration_vals[0]),
		                                  p25_start_timing + getattr(end_duration_definition, duration_vals[1]),
		                                  )



class FallInitiationBuilder(BaseFlowComponentBuilder):
	pass


class WinterBaseFlowBuilder(BaseFlowComponentBuilder):
	pass


class WinterPeakFlowBuilder(BaseFlowComponentBuilder):
	pass
