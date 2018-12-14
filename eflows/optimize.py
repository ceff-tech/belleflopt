import logging
import random

import numpy
from platypus import Problem, Real
from platypus.operators import Generator, Solution

from eflows import models

log = logging.getLogger("eflows.optimization")

random.seed = 20181214


class InitialFlowsGenerator(Generator):
	"""
		Generates initial flows based on the actual allocated flows
	"""
	def __init__(self):
		super(InitialFlowsGenerator, self).__init__()

	def generate(self, problem):
		solution = Solution(problem)

		initial_values = [huc.initial_available_water for huc in problem.hucs]
		values = []
		for value in initial_values:
			values.append(value * ((random.random()*0.2)+0.8))  # multiply *0.2 so that the scaling power is minimal (0<value<0.2), then add 0.8 so that it could shrink it by up to 20% - should mean all starting solutions are feasible

		solution.variables = values
		return solution


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
	def __init__(self, decision_variables=None, objectives=2, *args):
		"""

		:param decision_variables: when this is set to None, it will use the number of HUCs as the number of decision
			variables
		:param objectives:  default is two (total needs met, and min by species)
		:param args:
		"""

		self.hucs = models.HUC.objects.all()
		if not decision_variables:
			self.decision_variables = models.HUC.objects.count()
		else:
			self.decision_variables = decision_variables

		log.info("Number of Decision Variables: {}".format(self.decision_variables))
		super(HUCNetworkProblem, self).__init__(self.decision_variables, objectives, *args)  # pass any arguments through

		self.directions[:] = Problem.MAXIMIZE  # we want to maximize all of our objectives
		self.feasible = 1  # 1 = infeasible, 0 = feasible - store the value here because we'll reference it layer in a closure

		self.eflows_nfe = 0

		self.setUp()

	def setUp(self,):
		"""
			On top of init, let's make something that actually does the setup when we're ready to.
			This would also be used when resetting a run or something
		:return:
		"""

		self.make_constraint()

		self.types[:] = Real(0, 1000000)
		self.feasible = 1  # 1 = infeasible, 0 = feasible - store the value here because we'll reference it layer in a closure

		met_needs = {}

		available_species = {}
		for huc in self.hucs:  # prepopulate all the species so we can skip a condition later - don't use all species because it's possible that some won't be present. Only use the species in all the hucs
			for species in huc.assemblage.all():
				available_species[species.common_name] = 1

		self.available_species = available_species.keys()
		log.debug("Total Species in Area: {}".format(len(available_species.keys())))

		self.eflows_nfe = 0

	def make_constraint(self):
		def constraint_function(value):
			"""
				We want this here so it's a closure and the value from the class is in-scope without a "self"
			:return:
			"""

			return self.feasible  # this will be set during objective evaluation later

		self.constraints[:self.decision_variables+1] = constraint_function

	def set_types(self):
		"""
			Sets the type of each decision variable and makes it the max, should be in the same order that we
			assign flows out later, so the max values should allign with the allocations that come in.
		:return:
		"""
		allocation_index = 0
		hucs = self.hucs
		for huc in hucs:
			self.types[allocation_index] = Real(0, huc.max_possible_flow)
			allocation_index += 1

	def set_huc_allocations(self, allocations):

		allocation_index = 0
		hucs = self.hucs
		for huc in hucs:
			try:
				huc.flow_allocation = allocations[allocation_index]
			except IndexError:
				log.error("Size mismatch between number of HUCs and number of allocations - either"
						  "too many HUCs are loaded in the database, or there are too few decision"
						  "variables receiving allocations")
				raise

			allocation_index += 1
			# huc.save()  # let's see if we can skip this - lots of overhead in it.from

	def evaluate(self, solution):
		"""
			Alternatively, could build this so that it reports the number of hucs, per species and we construct our
			problem to be ready for that - we might not want that for actual use though, because that would lead to
			way too many resulting variables on the pareto front, etc, and would prevent a true tradeoff with economics.
			Options for this initial project :
				1) Average across the entire system and min needs met (min of the # hucs per species)
				 - that way we can see the overall benefit, but also make sure it's not zeroing out species to get there
		:param allocations:
		:return:
		"""

		if self.eflows_nfe % 5 == 0:
			log.info("NFE (inside): {}".format(self.eflows_nfe))
		self.eflows_nfe += 1

		# attach allocations to HUCs here - doesn't matter what order we do it in,
		# so long as it's consistent
		self.set_huc_allocations(allocations=solution.variables)

		met_needs = {}
		for species in self.available_species:
			met_needs[species] = 0

		### TODO: REWORK THIS SLIGHTLY FOR BOTH MINIMUM AND MAXIMUM FLOW - DON'T THINK IT'LL WORK AS IS.
		for huc in self.hucs:
			for species in huc.assemblage.all():  # for every species
				needs = []
				for component in models.SpeciesComponent.objects.filter(species=species, component__name="min_flow"):
					#if component.name == "min_flow":  # just do min flows for now
					needs.append(component.value*component.threshold)

				needs = numpy.array(needs)
				met_needs[species.common_name] += (needs < huc.flow_allocation).sum()  # / species.components.count()

		#all_met = [1 for species in met_needs.keys() if met_needs[species] > 0.99]
		all_met = sum([met_needs[species] for species in met_needs])
		min_met_needs = min([met_needs[species] for species in met_needs])

		self.check_constraints()  # run it now - it'll set a flag that'll get returned by the constraint function
		log.info("Feasibility: {}".format("Feasible" if self.feasible == 0 else "Infeasible"))
		solution.objectives[0] = all_met
		solution.objectives[1] = min_met_needs  # the total number of needs met
		solution.constraints[:self.decision_variables+1] = 99  # TODO: THIS MIGHT BE WRONG - THIS SET OF CONSTRAINTS MIGHT NOT
													# FOLLOW THE 0/1 feasible/infeasible pattern - should confirm

	def check_constraints(self):
		"""
			Just pseudocode now. This function should take as a parameter a watershed network. That network should be created
			and just return the indexes of the item and its upstream hucs in the allocation list. Then it can just subset
			and sum the list to get the total allocation, and compare that to the initial total allocation available for that
			same set of HUCs (same process - subset and sum inital allocations).

				Constraints:
					1) Current HUC can't use more than unused total water upstream + current HUC water.
					2) Current HUC + all upstream HUCs can't use more than total water upstream + current HUC water

				Other approach would be to zero out allocations, then go through and actually calculate the water available
				by summing the upstream allocations minus the used water, then just check each HUC against its allocation.
				The above is maybe simpler (and faster?), but maybe more prone to a logic error and less explicit. Must be
				documented regardless. The second approach would scale better to future constraints, where we loop through,
				calculate some parameters on each HUC, and then check the values against each HUC's constraints. We'll need
				some other logic changes before we do that, but they shouldn't be too bad.

			indexing code can happen before this and follow prior patterns.

			Also, initial available values should just come from zonal stats on a BCM raster. Low testing could be a summer
			flow and high testing a winter flow

			Need to run the constraint here once because when we check constraints, we won't be able
			to tell which item it's for, and it'll be run many times. We'll evaluate the network here, then set
			the constraint function to be a closure with access to the instance's constraint validity
			variable.
		:return:
		"""

		for huc in self.hucs:
			upstream_available = huc.upstream_total_flow
			upstream_used = sum([up_huc.flow_allocation for up_huc in huc.upstream.all() if up_huc.flow_allocation is not None])

			# first check - mass balance - did it allocate more water than is available?
			if (upstream_used + huc.flow_allocation) > (upstream_available + huc.initial_available_water):
				log.debug("Infeasible HUC: {}".format(huc.huc_id))
				log.debug("HUC Initial Available: {}".format(huc.initial_available_water))
				log.debug("HUC Allocation: {}".format(huc.flow_allocation))
				log.debug("Upstream Available: {}".format(upstream_available))
				log.debug("Upstream Used: {}".format(upstream_used))

				self.feasible = 1  # infeasible
				return

			# second check - is the current huc using more than is available *right here*?
			if huc.flow_allocation > (upstream_available + huc.initial_available_water - upstream_used):
				self.feasible = 1  # infeasible
				log.debug("infeasible 2")
				return

		# for now, if those two constraints are satisfied for all HUCs, then we're all set - set the contstraint
		# as valid (0)
		self.feasible = 0

