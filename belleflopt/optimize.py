import logging
import random
import collections
import os

import numpy
import pandas
from platypus import Problem, Real
from platypus.operators import Generator, Solution

from matplotlib import pyplot as plt

from belleflopt import models
from belleflopt import economic_components
from eflows_optimization.local_settings import PREGENERATE_COMPONENTS

log = logging.getLogger("eflows.optimization")

random.seed = 20200224


class SimpleInitialFlowsGenerator(Generator):
	"""
		Generates initial flows based on a constant proportion passed into the constructor
	"""
	def __init__(self, proportion):
		self.proportion = proportion
		super(SimpleInitialFlowsGenerator, self).__init__()

	def generate(self, problem):
		solution = Solution(problem)
		solution.variables = [self.proportion, ] * problem.decision_variables  # start with almost everything for the environment
		return solution


class InitialFlowsGenerator(Generator):
	"""
		Generates initial flows based on the actual allocated flows
	"""
	def __init__(self):
		super(InitialFlowsGenerator, self).__init__()

	def generate(self, problem):
		solution = Solution(problem)

		initial_values = [(random.random()*0.2)+0.8, ] * problem.decision_variables  # start with almost everything for the environment
		solution.variables = initial_values

		return solution


class SparseList(list):
	"""
	via https://stackoverflow.com/a/1857860/587938 - looks like a nice
	implemetation of a sparse list, which we'll want for when we do our
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


class ModelStreamSegment(object):
	"""
		# I think maybe we'd be better off making a simple tree structure here than relying on Django - should be much faster.
		# We can create the tree on model startup and it'll let us route daily flows through the network much faster.
		# we'll have a segment class with attributes for downstream instance, and we'll attach the django segment too so that we
		# can send off flows for evaluation without another lookup. If we give it its decision variable as an array and it
		# provides the extracted, local, and available downstream values, that's what we need (it can do the whole year at once).
		# We need a recursive function that allocates the flows through the network, looking upstream. It can stop and use the total
		# upstream that's already calculated once it hits spots that have already done it. PITA to redevelop this!

		# number of decision variables = number of segments in network * days in water year
		# numpy reshape it so that we have a 2 dimensional array with days in water year columns and n segments rows
		# each value is the proportion of available water we want to reserve in the stream for environmental flows
		# we have a similar array for locally available water. We then need to create the upstream water array from
		# traversing the network and doing the allocations to each segment and each segment's downstream. If we do that
		# and then translate it back out into a numpy array of the same shape, we can get a total water array (upstream + local)
		# then an environmental water array (total * decision variable array) and an economic water array(total * (1-decsion var array).
		# can then put the economic through a single benefit calculation from the economic benefit item to get total economic benefit.
		# for environmental benefit, we then need to iterate through each segment and give it its timeseries and have it return
		# the total benefit for that segment. We should track each segment's benefit and total economic benefit separately, and
		# also then sum all segment economic benefits together to get total environmental benefit.
	"""

	annual_allocation_proportion = None
	_local_available = numpy.zeros((365,))  # will be overridden when __init__ runs get_local_flows
	eflows_proportion = numpy.zeros((365,))

	def __init__(self, stream_segment, comid, network):
		self.comid = comid
		self.downstream = None
		self.upstream = []
		self._upstream_available = None
		self.stream_segment = stream_segment
		self.full_network = network

		self.get_local_flows()

	def get_local_flows(self):
		self._local_available = self._get_local_flows(use_property="estimated_local_flow")

		if self._local_available.shape[0] == 0:
			log.warning("No flows for segment {} - Removing from model because leaving it in means the model may fail! It may still fail if this removal results in a loss of connectivity".format(self.comid))
			raise RuntimeError("No flows for segment {}. Removing from model".format(self.comid))

	def _get_local_flows(self, use_property="estimated_local_flow"):
		local_flows_objects = models.DailyFlow.objects.filter(model_run=self.full_network.model_run,
		                                                      water_year=self.full_network.water_year,
		                                                      stream_segment=self.stream_segment) \
														.order_by("water_year_day")
		return numpy.array([float(getattr(day_flow, use_property)) for day_flow in local_flows_objects])

	@property
	def eflows_benefit(self):
		return self.stream_segment.get_benefit_for_timeseries(self.eflows_water, daily=False, collapse_function=numpy.max)

	@property
	def eflows_water(self):
		return self.eflows_proportion * self.local_available

	@property
	def economic_water(self):
		return (1 - self.eflows_proportion) * self.local_available

	@property
	def downstream_available(self):
		return self.eflows_water

	@property
	def local_available(self):
		"""
			How much water is available here from upsteam and local sources?
		:return:
		"""
		return self._local_available + self.upstream_available

	@property
	def raw_available(self):
		"""
			What's the raw daily flow, ignoring where it's coming from
		:return:
		"""

		return self._get_local_flows(use_property="estimated_total_flow")

	@property
	def upstream_available(self):
		"""
			How much water is available here from upstream?
		:return:
		"""
		if self._upstream_available is not None:  # short circuit, but if we don't have it then we need to get it.
			return self._upstream_available

		upstream_available = 0
		for upstream in self.upstream:
			upstream_available += upstream.downstream_available  # get the amount of water in the upstream item that flows downstream

		self._upstream_available = upstream_available
		return self._upstream_available

	def reset(self):
		"""
			resets the class for another evaluation round
		:return:
		"""
		self._upstream_available = None

	def set_allocation(self, allocation):
		self.eflows_proportion = allocation  # should be a numpy array with 365 elements

	def plot_results_with_components(self, screen=True, results=("raw_available", "eflows_water"),
	                                 skip_components=(), output_folder=None, name_prefix=None):
		"""
			Plots a flow timeseries with red boxes for each component for the segment
			layered on top. By default shows the eflows allocation, but by passing the name
			of the attribute as a string to "result", you can plot a different timeseries.
		:param screen:
		:param result:
		:return:
		"""

		components = self.stream_segment.segmentcomponent_set.all()
		fig, ax = plt.subplots(1)

		# they can provide a FlowComponent queryset/iterable to skip, get the IDs
		skip_components = [component.id for component in skip_components]

		for component in components:
			if component.component.id in skip_components:  # if the component ID matches one to skip, go to next
				continue

			try:
				rect = plt.Rectangle((component.start_day_ramp, component.minimum_magnitude_ramp),
				                     component.duration_ramp,
				                     component.maximum_magnitude_ramp - component.minimum_magnitude_ramp,
				                     linewidth=1, edgecolor='r', facecolor='none', fill=False)
			except TypeError:
				continue

			ax.add_patch(rect)

		# plotting by making a data frame first to try to get it to show a legend
		plot_data = {"Days": range(1, 366)}
		for result in results:
			plot_data[result] = getattr(self, result)

		pd_data = pandas.DataFrame(plot_data, columns=plot_data.keys())

		for result in results:
			ax.plot("Days", result, data=plot_data, label=result)

		ax.autoscale()

		eflows_water = sum(getattr(self, "eflows_water"))
		extracted = sum(getattr(self, "raw_available")) - eflows_water

		plt.title("{} {} - EF = {:.4}, Ext = {:.4}".format(self.stream_segment.com_id, self.stream_segment.name, eflows_water, extracted))

		ax.legend()

		if output_folder is not None:
			segment_name = "{}_{}_{}.png".format(name_prefix, self.stream_segment.com_id, self.stream_segment.name)
			output_path = os.path.join(output_folder, segment_name)
			plt.savefig(output_path)

		if screen:
			plt.show()
		else:
			plt.close()

		return fig, ax


class StreamNetwork(object):

	stream_segments = collections.OrderedDict()

	def __init__(self, django_segments, water_year, model_run, economic_benefit_instance=None):
		self.water_year = water_year
		self.model_run = model_run  # Django model run object

		self.economic_benefit_calculator = economic_benefit_instance
		self.build(django_segments)

	def build(self, django_segments):
		log.info("Initiating network and pulling daily flow data")

		if PREGENERATE_COMPONENTS:
			log.info("PREGENERATE_COMPONENTS is True, so network build will be slow")

		for segment in django_segments.all():
			try:
				self.stream_segments[segment.com_id] = ModelStreamSegment(segment, segment.com_id, network=self)
			except RuntimeError:  # We use RuntimeError to indicate a flow problem that this clause prevents - it raises a warning where the exception originates
				pass

		log.info("Making network connectivity")
		for segment in self.stream_segments.values():
			try:
				segment.downstream = self.stream_segments[segment.stream_segment.downstream.com_id]  # get the comid of the downstream object off the django object, then use it to index these objects
			except KeyError:
				log.warning("No downstream segment for comid {}. If this is mid-network, it's likely a problem, but it most"
				            "likely means this is the outlet".format(segment.stream_segment.com_id))

			for upstream in segment.stream_segment.directly_upstream.all():
				try:
					segment.upstream.append(self.stream_segments[upstream.com_id])  # then get the comid for the upstream item and use it to look up the item in this network
				except KeyError:
					log.warning("Missing upstream segment with comid {}. Likely means no flow data for segment, so it's left out."
					            "This could be a problem mid-network, but this most likely is a small headwaters tributary. You should"
					            "go look on a map.".format(upstream.com_id))

			segment.stream_segment.ready_run()  # attaches the benefit objects so that we can evaluate benefit

	def set_segment_allocations(self, allocations):
		self.reset()

		allocations = numpy.reshape(allocations, (-1, 365))

		allocation_index = 0
		for segment in self.stream_segments.values():
			segment.set_allocation(allocations[allocation_index])
			allocation_index += 1

	def get_benefits(self):
		environmental_benefits = [segment.eflows_benefit for segment in self.stream_segments.values()]
		eflow_benefit = numpy.sum(environmental_benefits)
		economic_water_total = numpy.sum([segment.economic_water for segment in self.stream_segments.values()])
		self.economic_benefit_calculator.units_of_water = economic_water_total
		economic_benefit = self.economic_benefit_calculator.get_benefit()

		#print("Available Water: {}".format(numpy.sum([segment._local_available for segment in self.stream_segments.values()])))
		#print("Env Water, Ben: {}, {}".format(numpy.sum([segment.eflows_water for segment in self.stream_segments.values()]), eflow_benefit))
		#print("Eco Water, Ben: {}, {}".format(economic_water_total, economic_benefit))

		# we could return the individual benefits here, but we'll save that for another time
		return {
			"environmental_benefit": eflow_benefit,
			"economic_benefit": economic_benefit,
		}

	def reset(self):
		for segment in self.stream_segments.values():
			segment.reset()


class StreamNetworkProblem(Problem):
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
				plus everything coming from upstream.
	"""
	def __init__(self, stream_network, starting_water_price=800, total_units_needed_factor=0.99, objectives=2, *args):
		"""

		:param decision_variables: when this is set to None, it will use the number of HUCs as the number of decision
			variables
		:param objectives:  default is two (total needs met, and min by species)
		:param args:
		"""

		self.stream_network = stream_network
		self.stream_network.economic_benefit_calculator = economic_components.EconomicBenefit(starting_water_price,
		                                                                                      total_units_needed=self.get_needed_water(total_units_needed_factor))
		self.decision_variables = len(stream_network.stream_segments) * 365  # we need a decision variable for every stream segment and day - we'll reshape them later

		self.iterations = []
		self.objective_1 = []
		self.objective_2 = []

		log.info("Number of Decision Variables: {}".format(self.decision_variables))
		super(StreamNetworkProblem, self).__init__(self.decision_variables, objectives, *args)  # pass any arguments through

		self.directions[:] = Problem.MAXIMIZE  # we want to maximize all of our objectives
		self.types[:] = Real(0, 1)  # we now construe this as a proportion instead of a raw value

		self.eflows_nfe = 0

	def reset(self):
		self.iterations = []
		self.objective_1 = []
		self.objective_2 = []
		self.eflows_nfe = 0

	def get_needed_water(self, proportion):
		"""
			Given a proportion of a basin's total water to extract, calculates the quantity
		:return:
		"""

		log.info("Calculating total water to extract")
		total_water = 0
		all_flows = self.stream_network.model_run.daily_flows.filter(water_year=self.stream_network.water_year)
		for flow in all_flows:
			total_water += flow.estimated_local_flow

		print("Total Water Available: {}".format(total_water))
		return float(total_water) * proportion

	def evaluate(self, solution):
		"""
			We want to evaluate a full hydrograph of values for an entire year
		"""

		if self.eflows_nfe % 5 == 0:
			log.info("NFE (inside): {}".format(self.eflows_nfe))
		self.eflows_nfe += 1

		# attach allocations to segments here - doesn't matter what order we do it in, so long as it's consistent
		self.stream_network.set_segment_allocations(allocations=solution.variables)

		benefits = self.stream_network.get_benefits()

		# set the outputs - platypus looks for these here.
		solution.objectives[0] = benefits["environmental_benefit"]
		solution.objectives[1] = benefits["economic_benefit"]

		# tracking values
		self.iterations.append(self.eflows_nfe)
		self.objective_1.append(benefits["environmental_benefit"])
		self.objective_2.append(benefits["economic_benefit"])


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
				plus everything coming from upstream.
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

		self.iterations = []
		self.objective_1 = []
		self.objective_2 = []

		log.info("Number of Decision Variables: {}".format(self.decision_variables))
		super(HUCNetworkProblem, self).__init__(self.decision_variables, objectives, nconstrs=1)  # pass any arguments through

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

		self.set_types()
		self.feasible = 1  # 1 = infeasible, 0 = feasible - store the value here because we'll reference it layer in a closure

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

		self.constraints[:] = constraint_function

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

		# initialize code to track how many flow needs are met per species
		met_needs = {}
		for species in self.available_species:
			met_needs[species] = 0

		### TODO: REWORK THIS SLIGHTLY FOR BOTH MINIMUM AND MAXIMUM FLOW - DON'T THINK IT'LL WORK AS IS.
		# Iterate through assemblages for all HUCs and evaluate which flow needs have been met.
		for huc in self.hucs:
			for species in huc.assemblage.all():  # for every species
				needs = []
				for component in models.SpeciesComponent.objects.filter(species=species, component__name="min_flow"):
					needs.append(component.value*component.threshold)

				needs = numpy.array(needs)
				met_needs[species.common_name] += (needs < huc.flow_allocation).sum()  # / species.components.count()

		# determine objective values
		all_met = sum([met_needs[species] for species in met_needs])
		min_met_needs = min([met_needs[species]/models.Species.objects.get(common_name=species).presence.count() for species in met_needs])

		self.check_constraints()  # run it now - it'll set a flag that'll get returned by the constraint function
		log.debug("Feasibility: {}".format("Feasible" if self.feasible == 0 else "Infeasible"))

		# set the outputs - platypus looks for these here.
		solution.objectives[0] = all_met
		solution.objectives[1] = min_met_needs  # the total number of needs met
		#solution.constraints[:self.decision_variables+1] = 99  # TODO: THIS MIGHT BE WRONG - THIS SET OF CONSTRAINTS MIGHT NOT
													# FOLLOW THE 0/1 feasible/infeasible pattern - should confirm

		# tracking values
		self.iterations.append(self.eflows_nfe)
		self.objective_1.append(all_met)
		self.objective_2.append(min_met_needs)

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

		## TODO: WHY ARE WE TREATING ENVIRONMENTAL FLOWS AS CONSUMPTIVE RELATIVE TO OTHER EFLOWS.
		## TODO: THEY SHOULD BE CONSUMPTIVE RELATIVE TO ECONOMIC USES, BUT NOT TO OTHER EFLOWS.

		for huc in self.hucs:
			upstream_available = huc.upstream_total_flow
			upstream_used = sum([up_huc.flow_allocation for up_huc in huc.upstream.all() if up_huc.flow_allocation is not None])

			# first check - mass balance - did it allocate more water than is available somewhere in the system?
			if (upstream_used + huc.flow_allocation) > (upstream_available + huc.initial_available_water):
				log.debug("Infeasible HUC: {}".format(huc.huc_id))
				log.debug("HUC Initial Available: {}".format(huc.initial_available_water))
				log.debug("HUC Allocation: {}".format(huc.flow_allocation))
				log.debug("Upstream Available: {}".format(upstream_available))
				log.debug("Upstream Used: {}".format(upstream_used))

				self.feasible = 1  # infeasible
				return 1

			# second check - is the current huc using more than is available *right here*?
			# I think this condition, as written, is the same as above - never triggered
			#if huc.flow_allocation > (upstream_available + huc.initial_available_water - upstream_used):
			#	self.feasible = 1  # infeasible
			#	log.debug("infeasible 2")
			#	return

		# for now, if those two constraints are satisfied for all HUCs, then we're all set - set the contstraint
		# as valid (0)
		self.feasible = 0
		return 0

