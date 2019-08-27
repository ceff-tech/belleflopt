
class BenefitBox(object):
    low_flow = None
    high_flow = None

    def single_flow_benefit(self, flow, margin=0.1):
        """
            Calculates the benefit of a single flow in relation to this box.
            We create 4 flow values with margins above and below the low and high flows.
            We then slope up to a benefit of 1 between the two lowflow points and down to a benefit of 0
            between the two highflow points.
        :param flow: The flow to get the benefit of
        :param margin: a multiplier (between 0 and 1) for determining how much space to use for generating the slope
                        as we ramp up and down benefits
        :return: continuous 0-1 benefit of input flow
        """

        window_size = self.high_flow - self.low_flow
        margin_size = int(margin * window_size)

        q1 = self.low_flow - margin_size
        q2 = self.low_flow + margin_size
        q3 = self.high_flow - margin_size
        q4 = self.high_flow + margin_size

        if flow < q1 or flow > q4:  # if it's way outside the window, benefit is 0
            return 0
        if q2 < flow < q3:  # if it's well in the window, benefit is 1
            return 1

        if q1 < flow < q2:  # benefit for ramping up near low flow
            slope = 1 / (q2 - q1)
            return slope * (flow - q1)
        else:  # only thing left is q3 < flow < q4 - benefit for ramping down at the high end of the box
            slope = 1 / (q4 - q3)
            return 1 - slope(flow - q3)
