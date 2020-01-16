import numpy

# Needs: 1 - way to convert CFS to acre-feet
#       2 - way to express marginal decrease in value of water based on current units


class EconomicBenefit(object):
	"""
		As currently designed, this class needs to be used BASIN-WIDE. That is, because it uses economic curves, it needs
		to have those be fed by water values for the whole system. So
	"""
	def __init__(self, starting_price, total_units_needed):
		self.starting_price = starting_price
		self.total_units_needed = total_units_needed
		self.units_of_water = 0
		self.unit_conversion_scaling_factor = 1

		self.vectorized_cost = numpy.vectorize(self._cost_of_water)

	def _convert_timeseries_units_to_water_units(self, ts_units):
		"""
			Converts the units of water in the timeseries (likely CFS) into units as specified here (acre feet??). This
			is kind of a fuzzy conversion since speed != volume, but we'll reasonably approximate for now.
		:param ts_units:
		:return:
		"""
		return ts_units * self.unit_conversion_scaling_factor

	def allocate_timeseries(self, timeseries):
		"""
			Each segment should call this with the timeseries allocation from the segment to withdraw water in that location.
			It stores the allocated water, and the cost (benefit) of that allocated water can be retrieved when all water
			is allocated with get_benefit.
		:param timeseries:
		:return:
		"""
		self.units_of_water += self._convert_timeseries_units_to_water_units(sum(timeseries))

	def get_benefit(self):
		"""
			In this case, cost (willingness to pay) reflects benefit since we're now in the economic realm.
		:param timeseries: The daily amount of water allocated for economic purposes across the basin
		:return:
		"""
		return self._cumulative_cost(self.units_of_water)

	def _cost_of_water(self, nth_unit):
		"""
			Implements the basic demand curve and provides the price of the nth unit of water.

			Base cost is -(starting_cost/units_needed)x + starting_cost, which ensures the starting price is starting_price
			and that by the time we get the number of units we need, the cost is 0. It's linear but would be easy enough
			to translate into a convex curve, which is probably more appropriate.
		:param nth_unit: The unit of water to get the price of. Taken sequentially, so 500 means that you want the cost
				of the 500th unit of water delivered, not that you want the price of 500 units of water
		:return:
		"""

		value = -(self.starting_price/self.total_units_needed) * nth_unit + self.starting_price
		return max(value, 0)  # we won't push the cost of water negative. If it goes negative, return 0.

	def _cumulative_cost(self, units):
		"""

		:param units: How many units of water do you want?
		:return:
		"""

		all_costs = self.vectorized_cost(range(1, units+1))
		return sum(all_costs)