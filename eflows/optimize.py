import numpy

from platypus import Problem

from eflows import models


class SparseList(list):
	"""
	via https://stackoverflow.com/a/1857860/587938 - looks like a nice
	implenetation of a sparse list, which we'll want for when we do our
	indexing and sums
	"""
	def __setitem__(self, index, value):
		missing = index - len(self) + 1
		if missing > 0:
			self.extend([None] * missing)
		list.__setitem__(self, index, value)

	def __getitem__(self, index):
		try:
			return list.__getitem__(self, index)
		except IndexError:
			return None


def check_constraints():
	"""
		Just pseudocode now. This function should take as a parameter a watershed network. That network should be created
		and just return the indexes of the item and its upstream hucs in the allocation list. Then it can just subset
		and sum the list to get the total allocation, and compare that to the initial total allocation available for that
		same set of HUCs (same process - subset and sum inital allocations).
			Constraints:
				1) Current HUC can't use more than total water upstream.
				2) Current HUC + all upstream HUCs can't use more than total water upstream

			Other approach would be to zero out allocations, then go through and actually calculate the water available
			by summing the upstream allocations minus the used water, then just check each HUC against its allocation.
			The above is maybe simpler (and faster?), but maybe more prone to a logic error and less explicit. Must be
			documented regardless. The second approach would scale better to future constraints, where we loop through,
			calculate some parameters on each HUC, and then check the values against each HUC's constraints. We'll need
			some other logic changes before we do that, but they shouldn't be too bad.

		indexing code can happen before this and follow prior patterns.

		Also, initial available values should just come from zonal stats on a BCM raster. Low testing could be a summer
		flow and high testing a winter flow
	:return:
	"""
	pass


class HUCNetworkProblem(Problem):
	"""
		We need to subclass this because:
			1) We want to save the HUCs so we don't load them every time - originally
				did this as a closure, but we *also* would like a class for
			2) Updating constraints for every solution. It's undocumented, but
				Platypus allows for *functions* as constraints, so we'll actually
				need a function that traverses the hydrologic network and returns 0 if
				the solution is feasible and 1 if it's not.

				Thinking that the constraint function will just traverse the network and make sure
				that flow value in each HUC is less than or equal to the sum of that HUC's initial flow
				plus everything upstream. T
	"""
	def __init__(self, *args):
		super(HUCNetworkProblem, self).__init__(*args)  # pass any arguments through
		self.hucs = models.HUC.objects.all()

		self.feasible = 1 # 1 = infeasible, 0 = feasible - store the value here because we'll reference it layer in a closure

	def objective(self, allocations):

		# attach allocations to HUCs here - doesn't matter what order we do it in,
		# so long as it's consistent

		def constraint_function():
			"""
				We want this here so it's a closure and the value from the class is in-scope without a "self"

				This might need to be moved somewhere else and just be generated before th problem is run
			:return:
			"""

			return self.feasible  # this will be set during objective evaluation later

		met_needs = {}

		for huc in self.hucs:
			for species in huc.assemblage:
				needs = []
				for component in species.components:
					needs.append(component.value*component.threshold)
				needs = numpy.array(needs)
				met_needs[species] = (needs < huc.flow_allocation).sum() / species.components.count()

		all_met = [1 for species in met_needs.keys() if met_needs[species] > 0.99]
		return sum(all_met)

	def constraint(self):
		"""
			Need to run the constraint here once because when we check constraints, we won't be able
			to tell which item it's for, and it'll be run many times. We'll evaluate the network here, then set
			the constraint function to be a lambda returning 0 (feasible) or 1 (infeasible)
		:return:
		"""


