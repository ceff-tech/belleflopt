from eflows_optimization import local_settings
from belleflopt import benefit


def _general_benefit_maker(segment_component):
	"""
		A benefit maker that can easily be used by components with simple timing and duration needs. Peak flows
		and spring recession may not be able to use it
	:param segment_component:
	:return:
	"""
	b = benefit.BenefitBox(component_name=segment_component.component.name,
	                       segment_id=segment_component.stream_segment.com_id)  # make a benefit box and set the magnitude q values immediately
	b.set_flow_values(segment_component.minimum_magnitude_ramp,
	                  segment_component.minimum_magnitude,
	                  segment_component.maximum_magnitude,
	                  segment_component.maximum_magnitude_ramp
	                  )
	b.set_day_values(segment_component.start_day_ramp,
	                 segment_component.start_day,
	                 segment_component.end_day,
	                 segment_component.end_day_ramp,
	                 )
	return b


def spring_recession_benefit_maker(segment_component):
	pass


def summer_base_flow_benefit_maker(segment_component):
	return _general_benefit_maker(segment_component)


def fall_initiation_benefit_maker(segment_component):
	pass


def winter_baseflow_benefit_maker(segment_component):
	return _general_benefit_maker(segment_component)


def winter_peak_flow_benefit_maker(segment_component):
	pass


### Builders
def _generic_builder(segment_component,
						magnitude_metric,
						start_timing_metric,
						duration_metric,
						start_timing_vals,
						duration_vals):
	"""
		This method needs serious testing.

		Given the set of flow metrics for a segment, builds the flow component out - provides a base way to do it
		for simple timing and duration defined components. Will not work for components that have frequency (peak flows)
		or recession rates.
	:param segment_component:
	"""
	# Get the flow metric values specific to this segment, that match what we need as defined in local_settings
	magnitude_definition = segment_component.metrics.get(flow_metric__metric=magnitude_metric)
	start_timing_definition = segment_component.metrics.get(flow_metric__metric=start_timing_metric)
	end_duration_definition = segment_component.metrics.get(flow_metric__metric=duration_metric)

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


def spring_recession_builder(segment_component):
	pass


def summer_base_flow_builder(segment_component,
							magnitude_metric=local_settings.SUMMER_BASEFLOW_MAGNITUDE_METRIC,
							start_timing_metric=local_settings.SUMMER_BASEFLOW_START_TIMING_METRIC,
							duration_metric=local_settings.SUMMER_BASEFLOW_DURATION_METRIC,
							start_timing_vals=local_settings.SUMMER_BASEFLOW_START_TIMING_VALUES,
							duration_vals=local_settings.SUMMER_BASEFLOW_DURATION_VALUES):
	_generic_builder(segment_component,
					magnitude_metric=magnitude_metric,
					start_timing_metric=start_timing_metric,
					duration_metric=duration_metric,
					start_timing_vals=start_timing_vals,
					duration_vals=duration_vals)


def fall_initiation_builder(segment_component):
	pass


def winter_base_flow_builder(segment_component,
							magnitude_metric=local_settings.WINTER_BASEFLOW_MAGNITUDE_METRIC,
							start_timing_metric=local_settings.WINTER_BASEFLOW_START_TIMING_METRIC,
							duration_metric=local_settings.WINTER_BASEFLOW_DURATION_METRIC,
							start_timing_vals=local_settings.WINTER_BASEFLOW_START_TIMING_VALUES,
							duration_vals=local_settings.WINTER_BASEFLOW_DURATION_VALUES):
	_generic_builder(segment_component,
					 magnitude_metric=magnitude_metric,
					 start_timing_metric=start_timing_metric,
					 duration_metric=duration_metric,
					 start_timing_vals=start_timing_vals,
					 duration_vals=duration_vals)


def winter_peak_flow_builder(segment_component,
							magnitude_metric=local_settings.WINTER_PEAK_MAGNITUDE_METRIC,
							start_timing_metric=local_settings.WINTER_PEAK_START_TIMING_METRIC,
							duration_metric=local_settings.WINTER_PEAK_DURATION_METRIC,
							start_timing_vals=local_settings.WINTER_PEAK_START_TIMING_VALUES,
							duration_vals=local_settings.WINTER_PEAK_DURATION_VALUES):

	return

	# _generic_builder(segment_component,
	#				magnitude_metric=magnitude_metric,
	#				start_timing_metric=start_timing_metric,
	#				duration_metric=duration_metric,
	#				start_timing_vals=start_timing_vals,
	#				duration_vals=duration_vals)
