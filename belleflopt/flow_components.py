import logging

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from eflows_optimization import local_settings
from belleflopt import benefit

log = logging.getLogger("belleflopt.")

# DO NOT IMPORT belleflopt.models - it would create a circular import


def _general_benefit_maker(segment_component, benefit_class=benefit.BenefitBox):
	"""
		A benefit maker that can easily be used by components with simple timing and duration needs. Peak flows
		and spring recession may not be able to use it
	:param segment_component:
	:return:
	"""
	b = benefit_class(component_name=segment_component.component.name,
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


def _general_peak_benefit_maker(segment_component, frequency_metric, frequency_value, peak_duration_metric, peak_value, peak_benefit_value):
	"""
		Generally, frequency_metric and frequency_value function as the rest of the functions in this module do - metric
		is the functional flow metric name to look up and the value is the percentile to use from the metric.

		However, if frequency_metric is None, then frequency_value is assumed to be the raw, actual value for frequency.
		This is useful for fall flows where there isn't a metric, it's just assumed there's one flushing event we're
		trying to achieve. E.g. frequency_metric=None, frequency_value=1 in that case.
	:param segment_component:
	:param frequency_metric:
	:param frequency_value:
	:param peak_duration_metric:
	:param peak_value:
	:param peak_benefit_value:
	:return:
	"""
	benefit_item = _general_benefit_maker(segment_component, benefit_class=benefit.PeakBenefitBox)

	if frequency_metric is not None:
		frequency_item = segment_component.descriptors.get(flow_metric__metric=frequency_metric)
		frequency = getattr(frequency_item, frequency_value)
	else:
		frequency = frequency_value
	peak_duration_item = segment_component.descriptors.get(flow_metric__metric=peak_duration_metric)

	benefit_item.setup_peak_flows(peak_frequency=frequency,
									median_duration=getattr(peak_duration_item, peak_value),
									max_benefit=peak_benefit_value)
	return benefit_item


def winter_peak_flow_benefit_maker(segment_component,
						frequency_metric=local_settings.WINTER_PEAK_EVENT_FREQUENCY_METRIC,
						frequency_value=local_settings.WINTER_PEAK_EVENT_FREQUENCY_VALUE,
						peak_duration_metric=local_settings.WINTER_PEAK_EVENT_DURATION_METRIC,
						peak_value=local_settings.WINTER_PEAK_EVENT_DURATION_VALUE,
						peak_benefit_value=local_settings.WINTER_PEAK_EVENT_STARTING_BENEFIT):

	return _general_peak_benefit_maker(segment_component,
										frequency_metric=frequency_metric,
										frequency_value=frequency_value,
										peak_duration_metric=peak_duration_metric,
										peak_value=peak_value,
										peak_benefit_value=peak_benefit_value)


def spring_recession_benefit_maker(segment_component,
									rate_of_change_metric=local_settings.SPRING_RECESSION_RATE_OF_CHANGE_METRIC,
									full_benefit_values=local_settings.SPRING_RECESSION_RATE_OF_CHANGE_FULL_VALUES,
									steep_benefit_values=local_settings.SPRING_RECESSION_RATE_OF_CHANGE_STEEP_VALUES,
									steep_reduction_factor=local_settings.SPRING_RECESSION_RATE_REDUCTION_VALUE,
									very_steep=local_settings.SPRING_RECESSION_RATE_STEEP_REDUCTION_VALUE,
									max_daily_rate=local_settings.SPRING_RECESSION_MAX_RATE,
									min_time_before_fail=local_settings.SPRING_RECESSION_MIN_TIME_BEFORE_MAX_RATE_FAIL,
                                    max_time_before_fail=local_settings.SPRING_RECESSION_MAX_TIME_BEFORE_MAX_RATE_FAIL):

	# set up the base benefit
	b = _general_benefit_maker(segment_component, benefit_class=benefit.RecessionBenefitBox)

	# make the tuples of actual rate of change values by retrieving them from the rate of change metric
	rate_of_change = segment_component.descriptors.get(flow_metric__metric=rate_of_change_metric)
	normal_rates = (float(getattr(rate_of_change, full_benefit_values[0])), float(getattr(rate_of_change, full_benefit_values[1])))
	steep_rates = (float(getattr(rate_of_change, steep_benefit_values[0])), float(getattr(rate_of_change, steep_benefit_values[1])))


	b.setup_recession_benefit(normal_rates=normal_rates,
								steep_rates=steep_rates,
								fail_rate_of_change=max_daily_rate,
								steep_reduction=steep_reduction_factor,
								very_steep_reduction=very_steep,
								min_time_before_fail=min_time_before_fail,
	                            max_time_before_fail=max_time_before_fail
	                          )

	return b


def summer_base_flow_benefit_maker(segment_component):
	return _general_benefit_maker(segment_component)


def fall_initiation_benefit_maker(segment_component,
									frequency_value=local_settings.FALL_INITIATION_FREQUENCY,
									peak_duration_metric=local_settings.FALL_INITIATION_DURATION_METRIC,
									peak_value=local_settings.FALL_INITIATION_EVENT_DURATION_VALUE,
									peak_benefit_value=local_settings.FALL_INITIATION_EVENT_STARTING_BENEFIT):

	return _general_peak_benefit_maker(segment_component,
										frequency_metric=None,
										frequency_value=frequency_value,
										peak_duration_metric=peak_duration_metric,
										peak_value=peak_value,
										peak_benefit_value=peak_benefit_value)


def winter_baseflow_benefit_maker(segment_component):
	return _general_benefit_maker(segment_component)


### Builders
def _generic_builder(segment_component,
						magnitude_metric,
						magnitude_values,
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
	try:
		# Get the flow metric values specific to this segment, that match what we need as defined in local_settings
		magnitude_definition = segment_component.descriptors.filter(flow_metric__metric=magnitude_metric).first()
		start_timing_definition = segment_component.descriptors.filter(flow_metric__metric=start_timing_metric).first()
		end_duration_definition = segment_component.descriptors.filter(flow_metric__metric=duration_metric).first()
	except ObjectDoesNotExist:  # if no metrics are assigned, we get ObjectDoesNotExist, so just return
		log.debug("No metrics assigned for segment_component with segment {} and component {}".format(segment_component.stream_segment.com_id, segment_component.component.name))
		return
	except MultipleObjectsReturned:
		log.debug("Multiple Objects Returned for segement component with comid {} and component {}".format(segment_component.stream_segment.com_id, segment_component.component.name))
		raise

	_generic_magnitude(segment_component, magnitude_definition, magnitude_values)

	_generic_timing_and_duration(segment_component, end_duration_definition, duration_vals, start_timing_definition,
	                             start_timing_vals)


def _generic_magnitude(segment_component, magnitude_definition, magnitude_values):
	segment_component.minimum_magnitude_ramp = getattr(magnitude_definition, magnitude_values[0])
	segment_component.minimum_magnitude = getattr(magnitude_definition, magnitude_values[1])
	segment_component.maximum_magnitude = getattr(magnitude_definition, magnitude_values[2])
	segment_component.maximum_magnitude_ramp = getattr(magnitude_definition, magnitude_values[3])


def _generic_timing_and_duration(segment_component, end_duration_definition, duration_vals, start_timing_definition,
                                 start_timing_vals):
	# get the actual start timing values, then calculate the end values using the start timing and duration (as defined by preferences in
	# local_settings), and set the q values based on these looked up values
	segment_component.start_day_ramp = getattr(start_timing_definition, start_timing_vals[0])
	segment_component.start_day = getattr(start_timing_definition, start_timing_vals[1])

	# the duration vals come in as a two-tuple in the form
	# ((1. main start timing base value, 2. main duration), (3. duration ramp start timing base value, 4. duration ramp value)
	# where base values could be the raw value from pct_10, pct_25, or pct_50, etc
	# and then then main duration values could be any pct_* value after the first one
	# in each case, ultimately pull item 1 from the start timing definition and add item 2 from the duration definition
	# similarly, we'll pull item 3 from start timing and add item 4 from duration.
	segment_component.duration_base = getattr(start_timing_definition, duration_vals[0][0])
	segment_component.duration_ramp_base = getattr(start_timing_definition, duration_vals[1][0])

	segment_component.duration = getattr(end_duration_definition, duration_vals[0][1])
	segment_component.duration_ramp = getattr(end_duration_definition, duration_vals[1][1])


def spring_recession_builder(segment_component,
								magnitude_top_metric=local_settings.SPRING_RECESSION_MAGNITUDE_TOP_METRIC,
								magnitude_bottom_metric=local_settings.SPRING_RECESSION_MAGNITUDE_BOTTOM_METRIC,
								magnitude_values=local_settings.SPRING_RECESSION_MAGNITUDE_VALUES,
								start_timing_metric=local_settings.SPRING_RECESSION_START_TIMING_METRIC,
								duration_metric=local_settings.SPRING_RECESSION_DURATION_METRIC,
								start_timing_vals=local_settings.SPRING_RECESSION_START_TIMING_VALUES,
								duration_vals=local_settings.SPRING_RECESSION_DURATION_VALUES):
	try:
		# Get the flow metric values specific to this segment, that match what we need as defined in local_settings
		magnitude_top_definition = segment_component.descriptors.get(flow_metric__metric=magnitude_top_metric)
		magnitude_bottom_definition = segment_component.descriptors.get(flow_metric__metric=magnitude_bottom_metric)
		start_timing_definition = segment_component.descriptors.get(flow_metric__metric=start_timing_metric)
		end_duration_definition = segment_component.descriptors.get(flow_metric__metric=duration_metric)
	except ObjectDoesNotExist:  # if no metrics are assigned, we get ObjectDoesNotExist, so just return
		log.debug("No metrics assigned for segment_component with segment {} and component {}".format(segment_component.stream_segment.com_id, segment_component.component.name))
		return
	except MultipleObjectsReturned:
		log.debug("Multiple Objects Returned for metrics for segment_component with comid {} and component {}".format(segment_component.stream_segment.com_id, segment_component.component.name))
		raise

	# we use different top and bottom metrics for magnitude, so need to do this manually, not with generic.
	segment_component.minimum_magnitude_ramp = getattr(magnitude_bottom_definition, magnitude_values[0])
	segment_component.minimum_magnitude = getattr(magnitude_bottom_definition, magnitude_values[1])
	segment_component.maximum_magnitude = getattr(magnitude_top_definition, magnitude_values[2])
	segment_component.maximum_magnitude_ramp = getattr(magnitude_top_definition, magnitude_values[3])

	_generic_timing_and_duration(segment_component, end_duration_definition, duration_vals, start_timing_definition,
									start_timing_vals)


def summer_base_flow_builder(segment_component,
							magnitude_metric=local_settings.SUMMER_BASEFLOW_MAGNITUDE_METRIC,
							magnitude_values=local_settings.SUMMER_BASEFLOW_MAGNITUDE_VALUES,
							start_timing_metric=local_settings.SUMMER_BASEFLOW_START_TIMING_METRIC,
							duration_metric=local_settings.SUMMER_BASEFLOW_DURATION_METRIC,
							start_timing_vals=local_settings.SUMMER_BASEFLOW_START_TIMING_VALUES,
							duration_vals=local_settings.SUMMER_BASEFLOW_DURATION_VALUES):
	_generic_builder(segment_component,
					magnitude_metric=magnitude_metric,
					magnitude_values=magnitude_values,
					start_timing_metric=start_timing_metric,
					duration_metric=duration_metric,
					start_timing_vals=start_timing_vals,
					duration_vals=duration_vals)


def fall_initiation_builder(segment_component,
							magnitude_metric=local_settings.FALL_INITIATION_MAGNITUDE_METRIC,
							magnitude_values=local_settings.FALL_INITIATION_MAGNITUDE_VALUES,
							start_timing_metric=local_settings.FALL_INITIATION_START_TIMING_METRIC,
							duration_metric=local_settings.FALL_INITIATION_START_TIMING_METRIC,
							start_timing_vals=local_settings.FALL_INITIATION_START_TIMING_VALUES,
							duration_vals=local_settings.FALL_INITIATION_DURATION_VALUES):
	"""
		NOTE: We INTENTIONALLY set START_TIMING into the duration_metric. It's not an accident or a bug/typo above.

		For fall initiation flows ONLY we use start timing for both timing and duration. Duration is more like peak
		duration, rather than duration of the time window. So, since durations will generally be short, we'll just use
		the start_timing to set the beginning and end of the window, then use duration as our normal peak calculations.
	"""

	return _generic_builder(segment_component,
					magnitude_metric=magnitude_metric,
					magnitude_values=magnitude_values,
					start_timing_metric=start_timing_metric,
					duration_metric=duration_metric,  # We INTENTIONALLY use start timing for duration here - see docstring
					start_timing_vals=start_timing_vals,
					duration_vals=duration_vals)


def winter_base_flow_builder(segment_component,
							magnitude_metric=local_settings.WINTER_BASEFLOW_MAGNITUDE_METRIC,
							magnitude_values=local_settings.WINTER_BASEFLOW_MAGNITUDE_VALUES,
							start_timing_metric=local_settings.WINTER_BASEFLOW_START_TIMING_METRIC,
							duration_metric=local_settings.WINTER_BASEFLOW_DURATION_METRIC,
							start_timing_vals=local_settings.WINTER_BASEFLOW_START_TIMING_VALUES,
							duration_vals=local_settings.WINTER_BASEFLOW_DURATION_VALUES):
	_generic_builder(segment_component,
					 magnitude_metric=magnitude_metric,
	                 magnitude_values=magnitude_values,
					 start_timing_metric=start_timing_metric,
					 duration_metric=duration_metric,
					 start_timing_vals=start_timing_vals,
					 duration_vals=duration_vals)


def winter_peak_flow_builder(segment_component,
							magnitude_metric=local_settings.WINTER_PEAK_MAGNITUDE_METRIC,
							magnitude_values=local_settings.WINTER_PEAK_MAGNITUDE_VALUES,
							start_timing_metric=local_settings.WINTER_PEAK_START_TIMING_METRIC,
							duration_metric=local_settings.WINTER_PEAK_DURATION_METRIC,
							start_timing_vals=local_settings.WINTER_PEAK_START_TIMING_VALUES,
							duration_vals=local_settings.WINTER_PEAK_DURATION_VALUES):

	# TODO: Need to make sure that winter peak frequency is correctly attached with the benefit maker

	# we can't use _generic_builder here without some difficulty and unnecessary re-engineering of it because two core
	# parts of peak flow (timing, duration) come from the baseflow. We'll pull those in here and utilize what we can
	# of the _generic_builder

	return _generic_builder(segment_component,
					magnitude_metric=magnitude_metric,
					magnitude_values=magnitude_values,
					start_timing_metric=start_timing_metric,
					duration_metric=duration_metric,
					start_timing_vals=start_timing_vals,
					duration_vals=duration_vals)
