from eflows_optimization import local_settings
from belleflopt import benefit


def spring_recession_benefit_maker(segment_component):
	pass


def summer_base_flow_benefit_maker(segment_component):
		b = benefit.BenefitBox()  # make a benefit box and set the magnitude q values immediately
		b.flow_item.set_values(segment_component.minimum_magnitude_ramp,
		                                  segment_component.minimum_magnitude,
		                                  segment_component.maximum_magnitude,
		                                  segment_component.maximum_magnitude_ramp
		                                  )
		b.date_item.set_values(segment_component.start_day_ramp,
		                                  segment_component.start_day,
		                                  segment_component.end_day,
		                                  segment_component.end_day_ramp,
		                                  )
		return b


def fall_initiation_benefit_maker(segment_component):
	pass


def winter_baseflow_benefit_maker(segment_component):
	pass


def winter_peak_flow_benefit_maker(segment_component):
	pass


### Builders
def spring_recession_builder(segment_component):
	pass


def summer_base_flow_builder(segment_component):
	"""
		This method needs serious testing.

		Gets the full set of q values for magnitude from one flow metric and makes a benefit object using those
		values. For timing, it pulls the start timing from one metric, and the duration from another. Which percentile
		it uses is configured in local_settings.

		This is abstracted to this class instead of being just a method on the main object because it allows for it to
		be overridden - it could just be a function instead of a class, as currently written. Consider if we just need
		functions for this
	:param segment_component:
	"""

	# Get the flow metric values specific to this segment, that match what we need as defined in local_settings
	magnitude_definition = segment_component.metrics.get(flow_metric__metric=local_settings.SUMMER_BASEFLOW_MAGNITUDE_METRIC)
	start_timing_definition = segment_component.metrics.get(flow_metric__metric=local_settings.SUMMER_BASEFLOW_START_TIMING_METRIC)
	end_duration_definition = segment_component.metrics.get(flow_metric__metric=local_settings.SUMMER_BASEFLOW_DURATION_METRIC)
	start_timing_vals = local_settings.SUMMER_BASEFLOW_START_TIMING_VALUES
	duration_vals = local_settings.SUMMER_BASEFLOW_DURATION_VALUES

	segment_component.minimum_magnitude_ramp = magnitude_definition.pct_10
	segment_component.minimum_magnitude = magnitude_definition.pct_25
	segment_component.maximum_magnitude = magnitude_definition.pct_75
	segment_component.maximum_magnitude_ramp = magnitude_definition.pct_90

	# get the actual start timing values, then calculate the end values using the start timing and duration (as defined by preferences in
	# local_settings), and set the q values based on these looked up values
	segment_component.start_day_ramp = getattr(start_timing_definition, start_timing_vals[0])
	segment_component.start_day = getattr(start_timing_definition, start_timing_vals[1])
	segment_component.duration = getattr(end_duration_definition, duration_vals[0])
	segment_component.duration_ramp = getattr(end_duration_definition, duration_vals[1])


def fall_initiation_builder(segment_component):
	pass


def winter_base_flow_builder(segment_component):
	pass


def winter_peak_flow_builder(segment_component):
	pass
