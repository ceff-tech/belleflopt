from matplotlib import pyplot as plt
import seaborn


class BenefitBox(object):
    _low_flow = None
    _high_flow = None
    start_day_of_water_year = None
    end_day_of_water_year = None

    # q1 -> q4 are calculated automatically whenever we set the margin
    _q1 = None
    _q2 = None
    _q3 = None
    _q4 = None
    _margin = None

    # using @properties for low_flow, high_flow, and margin so that we don't have to calculate q1->q4 every time we
    # check the benefit of something using this box. We can calculate those only on update of these parameters, then
    # just use them each time we check the benefit.
    @property
    def low_flow(self):
        return self._low_flow

    @low_flow.setter
    def low_flow(self, value):
        self._low_flow = value
        if self._high_flow and self._margin:
            self._update_qs()

    @property
    def high_flow(self):
        return self._high_flow

    @high_flow.setter
    def high_flow(self, value):
        self._high_flow = value
        if self._low_flow and self._margin:
            self._update_qs()

    @property
    def margin(self):
        return self._margin

    @margin.setter
    def margin(self, margin):
        if margin != self._margin:
            self._margin = margin
            if self._low_flow and self._high_flow:
                self._update_qs()

    def _update_qs(self):
        # otherwise, start constructing the window - find the size so we can build the ramping values.
        # see documentation for more description on how we build this
        window_size = self.high_flow - self.low_flow
        margin_size = int(self.margin * window_size)

        self._q1 = self.low_flow - margin_size
        self._q2 = self.low_flow + margin_size
        self._q3 = self.high_flow - margin_size
        self._q4 = self.high_flow + margin_size

    def single_flow_benefit(self, flow, flow_day=0, margin=0.1):
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

        # if we're not in the time range for this flow box, then there's no benefit
        # TODO: Issue 1 - this shouldn't be totally boolean, but a ramp up/down like below. See GitHub issue for more.
        if flow_day > self.end_day_of_water_year or flow_day < self.start_day_of_water_year:
            return 0

        if flow <= self._q1 or flow >= self._q4:  # if it's way outside the window, benefit is 0
            return 0
        if self._q2 <= flow <= self._q3:  # if it's well in the window, benefit is 1
            return 1

        if self._q1 < flow < self._q2:  # benefit for ramping up near low flow
            slope = 1 / (self._q2 - self._q1)
            return slope * (flow - self._q1)
        else:  # only thing left is q3 < flow < q4 - benefit for ramping down at the high end of the box
            slope = 1 / (self._q4 - self._q3)
            return 1 - slope * (flow - self._q3)

    def plot_benefit(self, min_flow=None, max_flow=None):

        # if they don't provide a min or max flow to plot, then set the values so that the box would be centered
        # with half the range on each side as 0s
        if not min_flow:
            min_flow = int(self.low_flow - (self.high_flow-self.low_flow)/2)
        if not max_flow:
            max_flow = int(self.high_flow + (self.high_flow-self.low_flow)/2)

        flows = range(min_flow, max_flow+1)

        # could also do this by just plotting (0,0) and the benefits at each q point, but this is easier to code
        benefits = map(self.single_flow_benefit, flows)

        plot = seaborn.lineplot(flows, benefits)
        plt.xlabel("Flow/Q (CFS)")
        plt.ylabel("Benefit")

        # add vertical lines for the low and high benefit flows
        plt.axvline(self.low_flow, 0, 1, dashes=(5, 8))
        plt.axvline(self.high_flow, 0, 1, dashes=(5, 8))

        # add points for the qs
        plt.scatter([self._q1, self._q2, self._q3, self._q4], [0, 1, 1, 0])

        # label the qs
        plt.text(self._q1 + 6, -0.015, "q1", fontsize=9, fontstyle="italic")
        plt.text(self._q2 - 19, 0.985, "q2", fontsize=9, fontstyle="italic")
        plt.text(self._q3 + 6, 0.985, "q3", fontsize=9, fontstyle="italic")
        plt.text(self._q4 - 19, -0.015, "q4", fontsize=9, fontstyle="italic")
        plt.show()
