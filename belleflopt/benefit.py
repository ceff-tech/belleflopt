import functools

import numpy
from matplotlib import pyplot as plt
import seaborn
from matplotlib.colors import ListedColormap

from eflows_optimization.settings import DEFAULT_COLORRAMP


class BenefitItem(object):
    """
        Could be the benefit on a day of the year or of a specific flow. Has a window of values
        and a margin over which benefit goes from 0-1 at the edges of those values. Calculates
        benefit for specific values based on this window and that margin. Abstracted here so
        that we can use if for dates or flows, but the locations of the "corners" still use
        the "q" terminology from the flows.
    """
    _low_bound = None
    _high_bound = None

    # q1 -> q4 are calculated automatically whenever we set the margin
    _q1 = None
    _q2 = None
    _q3 = None
    _q4 = None
    _q1_rollover = None
    _q2_rollover = None
    _q3_rollover = None
    _q4_rollover = None
    _margin = None
    rollover = None  # at what value should we consider it equivalent to 0?

    max_benefit = 1  # in most cases, this will be true, but it might get reconfigured for peak flows

    # using @properties for low_flow, high_flow, and margin so that we don't have to calculate q1->q4 every time we
    # check the benefit of something using this box. We can calculate those only on update of these parameters, then
    # just use them each time we check the benefit.
    @property
    def low_bound(self):
        return self._low_bound

    @low_bound.setter
    def low_bound(self, value):
        self._low_bound = value
        if self._high_bound is not None and self._margin is not None:
            self._update_qs()

    @property
    def high_bound(self):
        return self._high_bound

    @high_bound.setter
    def high_bound(self, value):
        self._high_bound = value
        if self._low_bound is not None and self._margin is not None:
            self._update_qs()

    @property
    def margin(self):
        return self._margin

    @margin.setter
    def margin(self, margin):
        if margin != self._margin:
            self._margin = margin
            if self._low_bound is not None and self._high_bound is not None:
                self._update_qs()

    def set_values(self, q1, q2, q3, q4):
        """
            Lets you explicitly set the q values if there is logic elsewhere that defines them
        :return:
        """
        self._q1 = q1
        self._q2 = q2
        self._q3 = q3
        self._q4 = q4

        self._check_rollover()

    def _check_rollover(self):
        """
            If any values go over the rollover, then modulos them back into the frame
        :return:
        """

        if self.rollover is None:
            return

        for item in ("_q2", "_q3", "_q4"):  # first, make sure the items are sequential by adding in the rollover value to anything coming in below the beginning
            if getattr(self, item) < self._q1:
                setattr(self, item, getattr(self, item) + self.rollover)  # this will get partially undone in the next block, but this way, we can use one set of logic no matter whether values are set manually and sequentially, or based on day of water year

        for item in ("_q1", "_q2", "_q3", "_q4"):
            setattr(self, "{}_rollover".format(item), getattr(self, item))
            setattr(self, item, int(getattr(self, item) % self.rollover))  # set each q to its modulo relative to 365

    def _update_qs(self):
        # otherwise, start constructing the window - find the size so we can build the ramping values.
        # see documentation for more description on how we build this
        window_size = abs(self.high_bound - self.low_bound)
        margin_size = int(self.margin * window_size)  # this coerces to int so that we can attach to whole flows and days - very small error introduced, but only if we don't manually define qs? May be able to coerce to float instead? It might be a Decimal

        if self.rollover and self.high_bound == self.rollover and self.low_bound == 0:
            # if the upper bound is the same as the limit (the rollover value), and the low bound is 0, then make the edges square, because the benefit is always 1
            self._q3 = self._q4 = self.high_bound
            self._q1 = self._q2 = self.low_bound
            return

        self._q1 = self.low_bound - margin_size
        self._q2 = self.low_bound + margin_size
        self._q3 = self.high_bound - margin_size
        self._q4 = self.high_bound + margin_size

        self._check_rollover()

    def plot_window(self):
        """
            Provides the safe margins for plotting.
        :return:
        """

        if self.rollover is not None and self._q4 < self._q1:
            return 0, self.rollover

        buffer = int(abs(self._q4 - self._q1)/4)
        min_value = min(self._q1, self._q2, self._q3, self._q4)
        max_value = max(self._q1, self._q2, self._q3, self._q4)
        low_value = int(max(0, min_value - buffer))
        if self.rollover is not None:
            high_value = min(self.rollover, max_value + buffer)
        else:
            high_value = int(max_value + buffer)

        return low_value, high_value

    def single_value_benefit(self, value, margin):
        """
            Calculates the benefit of a single flow in relation to this box.
            We create 4 flow values with margins above and below the low and high flows.
            We then slope up to a benefit of 1 between the two lowflow points and down to a benefit of 0
            between the two highflow points.
        :param flow: The flow to get the benefit of
        :param flow_day: the day of water year for which this flow is allocated
        :param margin: a multiplier (between 0 and 1) for determining how much space to use for generating the slope
                        as we ramp up and down benefits. It would be best if margin was defined based upon the actual
                        statistical uncertainty of the bounding box
        :return: continuous 0-1 benefit of input flow
        """

        self.margin = margin  # set it this way, and it will recalculate q1 -> q4 only if it needs to

        value = value if not self.rollover or value >= self._q1 else value + self.rollover
        if self._q4 < self._q1:
            q1 = self._q1_rollover
            q2 = self._q2_rollover
            q3 = self._q3_rollover
            q4 = self._q4_rollover
        else:
            q1 = self._q1
            q2 = self._q2
            q3 = self._q3
            q4 = self._q4

        if q2 <= value <= q3:  # if it's well in the window, benefit is 1
            # this check should be before the next one to account for always valid windows (ie, q1 == q2 and q3 == q4)
            return self.max_benefit
        if value <= q1 or value >= q4:  # if it's way outside the window, benefit is 0
            return 0

        if q1 < value < q2:  # benefit for ramping up near low flow
            slope = self.max_benefit / (q2 - q1)
            return slope * (value - q1)
        else:  # only thing left is q3 < flow < q4 - benefit for ramping down at the high end of the box
            slope = self.max_benefit / (q4 - q3)
            return self.max_benefit - slope * (value - q3)


class BenefitBox(object):

    low_flow = None
    high_flow = None

    start_day_of_water_year = None
    end_day_of_water_year = None

    flow_item = None
    date_item = None

    _annual_benefit = None

    def __init__(self, low_flow=None,
                 high_flow=None,
                 start_day_of_water_year=None,
                 end_day_of_water_year=None,
                 flow_margin=0.1,
                 date_margin=0.1,
                 component_name=None,
                 segment_id=None):

        self.component_name = component_name
        self.segment_id = segment_id

        self.low_flow = low_flow
        self.high_flow = high_flow
        self.start_day_of_water_year = start_day_of_water_year
        self.end_day_of_water_year = end_day_of_water_year

        self.flow_item = BenefitItem()
        self.flow_item.low_bound = self.low_flow
        self.flow_item.high_bound = self.high_flow
        self.flow_item.margin = flow_margin

        self.date_item = BenefitItem()
        self.date_item.low_bound = self.start_day_of_water_year
        self.date_item.high_bound = self.end_day_of_water_year
        self.date_item.rollover = 365  # tell it that the last day of the year is equal to the first
        self.date_item.margin = date_margin

        # make the vectorized function we'll use for time series
        self.vectorized_single_day_flow_benefit = numpy.vectorize(self.single_flow_benefit, otypes=[float])

    @property
    def name(self):
        if self.component_name and self.segment_id:
            return "{} on segment {}".format(self.component_name, self.segment_id)
        else:
            return "Flow Component - Flow: ({}, {}), DOY: ({}, {})".format(self.low_flow,
                                                            self.high_flow,
                                                            self.start_day_of_water_year,
                                                            self.end_day_of_water_year,)

    def single_flow_benefit(self, flow, day_of_year, flow_margin=None, date_margin=None):
        if not flow_margin:
            flow_margin = self.flow_item.margin
        if not date_margin:
            date_margin = self.date_item.margin

        flow_benefit = self.flow_item.single_value_benefit(value=flow, margin=flow_margin)
        time_benefit = self.date_item.single_value_benefit(value=day_of_year, margin=date_margin)

        return float(flow_benefit) * time_benefit

    def set_flow_values(self, *values):
        """
            Provides an interface to manually set the q values for the flow item. Provide four values (not as an iterable,
            as individual items) and this sets the flow q values, as well as setting the low/high bounds on this item
            as they would have been set if this item had been manually computed. The margin will still be inaccurate,
            but low and high will be halfway in-between the set values. Order of provided values should be q1, q2, q3, q4
        :param values: 4 individual flow values for q1, q2, q3, and q4
        :return: None
        """
        self.flow_item.set_values(*values)
        self.low_flow = values[1] - (values[1] - values[0]) / 2
        self.high_flow = values[3] - (values[3] - values[2]) / 2
        self._annual_benefit = None  # reset annual benefit to nothing since we just changed all the parameters

    def set_day_values(self, *values):
        """
            Provides an interface to manually set the q values for the day of year item. Provide four values (not as an iterable,
            as individual items) and this sets the day q values, as well as setting the low/high bounds on this item
            as they would have been set if this item had been manually computed. The margin will still be inaccurate,
            but low and high will be halfway in-between the set values. Order of provided values should be q1, q2, q3, q4
        :param values: 4 individual day of year values for q1, q2, q3, and q4
        :return: None
        """
        self.date_item.set_values(*values)
        self.start_day_of_water_year = values[1] - abs((values[1] - values[0]) / 2)
        self.end_day_of_water_year = values[3] - abs((values[3] - values[2]) / 2)
        self._annual_benefit = None  # reset annual benefit to nothing since we just changed all the parameters

    def recalculate_annual_benefit(self):
        """
            Forces the annual benefit surface to be rebuilt, even if it would otherwise try to use the cached copy.
        :return:
        """
        self.annual_benefit(force=True)

    @property
    def annual_benefit(self, force=False):
        """
            Computes an annual benefit surface, but only if one hasn't been set already. It avoids recalculating it
            because it's time intensive, unless force is True. If setting q values using appropriate methods (set_flow_values
            and set_day_values) then this surface is automatically recalculated when needed, but if other paramters
            are changed, then you must call recalculate_annual_benefit to force a recalculation.
            :param force: when True, automatically recalculates the annual benefit surface. When False, uses existing
                calculating if one exists. Default is False
        :return:
        """
        if self._annual_benefit is not None or force:
            return self._annual_benefit

        date_max = self.date_item.plot_window()[1]
        flow_max = self.flow_item.plot_window()[1]
        days, flows = numpy.indices((date_max, flow_max))  # get the indices to pass through the vectorized function as flows and days
        self._annual_benefit = self.vectorized_single_day_flow_benefit(flows, days)
        return self._annual_benefit

    def get_benefit_for_timeseries(self, timeseries):
        """
            Supplies the full benefit *just for this component* across a year given a day of water year-based timeseries
            of flows (so index 0 == October 1, index 1 == October 2, ... index 364 == September 30)

            Performance-wise, this still requires us to do computations for days that aren't part of this component - if
            we can figure out a way to just fill zeroes, then replace with values only for the days we need, could be
            faster.

            This is also just a *default* implementation - it works for base flows, but for peak flows, each day
            will depend on the previous day, so we'd probably generate the vectorized benefit, then adjust values
            based on peak flow component adjustment parameters
        :param timeseries:
        :return:
        """
        days = range(1, 366)  # index 0 == day 1 of water year, index 364 == day 365 of water year
        return self.vectorized_single_day_flow_benefit(timeseries, days)

    def plot_flow_benefit(self, min_flow=None, max_flow=None, day_of_year=100, screen=True):
        """

        :param min_flow:
        :param max_flow:
        :param day_of_year:
        :param screen: When True, displays the plot on the screen
        :return: matplotlib.pyplot plot object
        """

        # if they don't provide a min or max flow to plot, then set the values so that the box would be centered
        # with half the range on each side as 0s
        if not min_flow:
            min_flow = int(self.low_flow - (self.high_flow-self.low_flow)/2)
        if not max_flow:
            max_flow = int(self.high_flow + (self.high_flow-self.low_flow)/2)

        flows = range(min_flow, max_flow+1)

        # could also do this by just plotting (0,0) and the benefits at each q point, but this is easier to code
        benefits = map(functools.partial(self.single_flow_benefit, day_of_year=day_of_year), flows)

        plot = seaborn.lineplot(flows, benefits)
        plt.xlabel("Flow/Q (CFS)")
        plt.ylabel("Benefit")

        # add vertical lines for the low and high benefit flows
        #plt.axvline(self.low_flow, 0, 1, dashes=(5, 8))
        #plt.axvline(self.high_flow, 0, 1, dashes=(5, 8))

        # add points for the qs
        q2_benefit = self.single_flow_benefit(self.flow_item._q2, day_of_year=day_of_year)
        q3_benefit = self.single_flow_benefit(self.flow_item._q3, day_of_year=day_of_year)
        plt.scatter([self.flow_item._q1, self.flow_item._q2, self.flow_item._q3, self.flow_item._q4], [0, q2_benefit, q3_benefit, 0])

        # label the qs
        plt.text(self.flow_item._q1 + 6, -0.015, "q1", fontsize=9, fontstyle="italic")
        plt.text(self.flow_item._q2 - 19, q2_benefit - 0.015, "q2", fontsize=9, fontstyle="italic")
        plt.text(self.flow_item._q3 + 6, q3_benefit - 0.015, "q3", fontsize=9, fontstyle="italic")
        plt.text(self.flow_item._q4 - 19, -0.015, "q4", fontsize=9, fontstyle="italic")

        plt.ylim(-0.05, 1.05)
        plt.title("Benefit for {} on day {}".format(self.name, day_of_year))
        if screen:
            plt.show()

        return plot

    def plot_annual_benefit(self, screen=True, palette=ListedColormap(seaborn.color_palette(DEFAULT_COLORRAMP))):

        plot = plt.imshow(numpy.swapaxes(self.annual_benefit, 0, 1),
                   cmap=palette,
                   aspect="auto",  # allows it to fill the whole plot - by default keeps the axes on the same scale
                   vmin=0,  # force the data minimum to 0 - this should happen anyway, but let's be explicit
                   vmax=1,  # force the color scale to top out at 1, not at the data max
                   )
        plt.ylim(*self.flow_item.plot_window())
        plt.xlim(*self.date_item.plot_window())
        plt.title("Annual benefit for {} on segment {}".format(self.component_name, self.segment_id))
        plt.ylabel("Flow/Q (CFS)")
        plt.xlabel("Day of Water Year")
        plt.colorbar()
        if screen:
            plt.show()

        return plot


class PeakBenefitBox(BenefitBox):
    """
        Handles benefit for peak flows.

        Needs the peak magnitude and timing, but also two duration metrics. First duration is the window
        duration. Second duration is for the duration of any specific event.
    """

    peak_frequency = None
    peak_interevent_decay_factor = None  # how rapidly should the benefit between peak events decay? - will be calculated
                                            # from peak_frequency

    max_benefit = None  # how much benefit should the first day of the first peak event of this kind generate? This
                        # might be different for each kind of peak event (winter vs fall) - this value should be > 1
                        # to incentivize entering the peak flow

    peak_duration = None
    peak_intraevent_reduction_factor = None  # will be 1/peak duration, but this way we only calculate it once

    def _get_component_size(self):
        """
            Not currently used - gets the length of time the component lasts
        :return:
        """
        if self.start_day_of_water_year < self.end_day_of_water_year:
            return self.end_day_of_water_year - self.start_day_of_water_year
        else:
            return 365 - self.start_day_of_water_year + self.end_day_of_water_year

    def setup_peak_flows(self, peak_frequency, median_duration, max_benefit, minimum_max_benefit=0.25):
        """
            we'll calculate the interevent decay factor by taking max_benefit/median_frequency. max_benefit will be reduced
             by this value each time a peak flow event occurs. This way, in a median year, by the time we got to the end
             of the season, there'd be no benefit in additional peak flow events
        :param peak_frequency:  The number of times a peak event occurs in any given water year
        :param median_duration:
        :param max_benefit:
        :parameter minimum_max_benefit: Used when many peak flow events have occurred in the same water year - the benefit
                            bottoms out, and instead of going to 0, this is used instead.
        :return:
        """
        self.max_benefit = max_benefit
        self.peak_duration = median_duration
        self.minimum_max_benefit = minimum_max_benefit

        self.peak_intraevent_reduction_factor = 1 / float(self.peak_duration)

        self.peak_interevent_decay_factor = max_benefit/peak_frequency  # divide the max benefit by the number of times
                                                    # we're supposed to hit peak in a given year - we'll subtract this
                                                    # amount after every event.

    def get_peak_benefit(self, base_benefit, day_of_current_event, max_benefit):
        """
                Time window should be based on wet season baseflow timing and duration

                Calculation of peak interevent decay factor should be based on Peak_Fre metric, which describes how often peak
                events should occur.

                Calculation of peak intraevent decay factor should be based on Peak_Dur metric. Simplest case would be that
                we drop it linearly by (1/median_Peak_Dur * Max_Benefit) per day. If Peak_Dur was 4 and max benefit was 10 and
                this is the first event of the season, then we get the following benefit behavior:
                Day 0) 10  <- This is the start of the sequence, so it's 10 at the beginning of the peak flow, at moment 0
                Day 1) 7.5
                Day 2) 5
                Day 3) 2.5
                Day 4) 0 <- How do we handle this? We don't want to go to zero - benefit is greater than 0, but should be less
                            than 1 to incentivize a return to baseflow

                So, we could instead do an exponential decay of the form
                y = max_benefit^(-(1/median_Peak_Dur)*(x-median_Peak_Dur)) + min_benefit
                So, in the same scenario, if we define a minimum benefit of 0.5 where it asymptotes out, we get an equation like
                y = 10^(-0.25(x-4)) + 0.5, which yields results like:
                Day 0) 10.5
                Day 1) ~6.1
                Day 2) ~ 3.66
                Day 3) ~ 2.28
                Day 4) ~ 1.5
                Day 5) ~ 1
                Day 6) ~ 0.8

                But maybe we don't need a minimum benefit here - it distorts an otherwise great curve above, and because it's
                an exponential decay, we won't actually hit 0 or get close to it for a while. Maybe we should just do
                y = 10^(-0.25(x-4)), which yields:
                Day 0) 10
                Day 1) ~5.6
                Day 2) ~ 3.16
                Day 3) ~ 1.78
                Day 4) 1
                Day 5) ~ 0.56
                Day 6) ~ 0.32

                I like this approach the most - it approaches 0 around day 10, but for something that's supposed to be a
                4 day event, 10 days might not provide much benefit. It doesnt' really account for the uncertainty in the
                statistical modeling though - the model might try to force things back to baseflow after exactly the median
                value. But that might be OK for our purposes.

                Then, we can still reduce consecutive events benefit linearly from max, and just change the base of the
                exponential function. If the base reaches 1 or less, then we just assign a fixed value of less than 1 because
                this function becomes a straight line at 1.
            """
        ben = float(base_benefit) * (float(max_benefit) ** (-float(self.peak_intraevent_reduction_factor) * float(day_of_current_event - self.peak_duration)))
        print(ben)
        return ben

    def get_benefit_for_timeseries(self, timeseries):
        """
            Supplies the full benefit *just for this component* across a year given a day of water year-based timeseries
            of flows (so index 0 == October 1, index 1 == October 2, ... index 364 == September 30)

            This version overrides the parent implementation of this function - we won't call the parent - we don't need
            to - this should return the benefit by day on its own.
        :param timeseries:
        :return:
        """
        days = range(1, 366)  # index 0 == day 1 of water year, index 364 == day 365 of water year
        original_base_benefit = self.vectorized_single_day_flow_benefit(timeseries, days)

        days_in_peak = 0  # how many days long is the current peak_flow event
        current_max_benefit = self.max_benefit  # what's the max benefit available to a new peak flow event?

        base_daily_benefit = [0, ] * 365
        for day, benefit in enumerate(original_base_benefit):
            if benefit > 0:  # basically, we're in the peak box
                if current_max_benefit <= 1:  # max benefit of 1 is a flat line in this equation, and won't decay.
                                                # Max benefits below 1 will actually cause the benefit to increase with
                                                # days in the peak benefit equation
                    base_daily_benefit[day] = self.minimum_max_benefit
                else:
                    base_daily_benefit[day] = self.get_peak_benefit(benefit, days_in_peak, current_max_benefit)
                days_in_peak += 1  # add 1 to the current event
            else:  # benefit = 0, reset peak calcs
                if days_in_peak > 0:  # if we were in a peak event, we need to reduce max benefit for the next event
                    current_max_benefit -= self.peak_interevent_decay_factor
                    current_max_benefit = max(self.minimum_max_benefit, current_max_benefit)  # if somehow current_max
                        # _benefit got to be super low, bump it to some value, but keep it lower than base flow.
                        # this value will also trigger using itself as a constant benefit value above because if it was
                        # used as the base in an exponential equation, benefit would increase by day

                days_in_peak = 0  # reset counter for next flow event

        return original_base_benefit, base_daily_benefit  # now contains peak benefits, not base benefit
