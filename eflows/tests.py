import logging

import matplotlib.pyplot as plt
from platypus import NSGAII
from platypus.evaluator import MultiprocessingEvaluator

from django.test import TestCase

from . import models
from . import support
from . import optimize

log = logging.getLogger("eflows.optimization.tests")


class TestHUCNetwork(TestCase):

	def setUp(self):
		support.load_hucs()

	def _print_and_check_huc_info(self, ID, name, expected_upstream):

		tow = models.HUC.objects.get(huc_id=ID)
		log.debug("{} {} has {} upstream hucs".format(name, ID, tow.upstream.count()))
		log.debug("upstream HUCs, if any, are {}".format([huc.huc_id for huc in tow.upstream.all()]))
		self.assertEqual(tow.upstream.count(), expected_upstream)

	def test_huc_load(self):

		ridgeline_huc = "180101050801"  # 0 upstream
		small_upstream_huc = "180101050803"  # 2 upstream
		mid_upstream_huc = "180101050906"  # 11 upstream

		self._print_and_check_huc_info(ridgeline_huc, "Ridgeline HUC", 0)
		self._print_and_check_huc_info(small_upstream_huc, "Small Upstream", 2)
		self._print_and_check_huc_info(mid_upstream_huc, "Mid Upstream", 11)

	def test_species_load(self):
		support.load_species()

		flow_sensitive = ["CGO01", "CCK01", "CGC01", "SOT04", "CLS01", "SOM05",
							"SOK01", "SOT08", "SOT07", "SOT06", "SOT05", "OHP01",
							"CCM02", "CMC01", "GGA02", "CLS09", "SOM13", "PLH01",
							"SOM04", "SOM03", "PES01", "CCS01", "SOC03", "CCP01",
							"CRO02", "OST01", "CCL01", "CCK02", "CCM01", "CLE03",
							"CCO03", "SPW01", "SOM02", "SOM01", "AAM01", "CLS08",
							"GEN01", "CCR02", "CRO04", "CSB06", "PET01", "CCP02",
							"CXT01", "CLS02", "CCG01", "PLA01", "CLE01", "CAI01",
							"CPG01", "CRO01", "CPM01", "CCO01", "EHT01", "CRO07",
							"CCS02", "CCB01", "SOM07", "SOM08", "SOK02", "CLS05",
							"AAM02", "GEK01", "GGA03", "CCK03", "SOT01", "SOT02",
							"PLR01", "AAT01"]

		not_found = 0
		for fid in flow_sensitive:
			try:
				models.Species.objects.get(pisces_fid=fid)  # just make sure we can get it
			except models.Species.DoesNotExist:
				log.debug("{} not in database".format(fid))
				not_found += 1

		# There are 55 flow sensitive species not in the Eel (of 68)
		print("Not found species: {}".format(not_found))

		# This isn't a great test, but it'll do for now - probably worth expanding in the future
		# if we continue using this (as opposed to loading data straight from PISCES)
		self.assertEqual(not_found, 55)

	def test_flow_available(self):
		support.load_climate()

		for huc in models.HUC.objects.all():
			self.assertIsNotNone(huc.initial_available_water)
			self.assertGreaterEqual(huc.initial_available_water, 0)


class TestOptimization(TestCase):
	def setUp(self):
		support.reset()  # loads everything into the DB

	def test_optimize(self):

		problem = optimize.HUCNetworkProblem()
		NFE = 5
		popsize = 5
		self.eflows_opt = NSGAII(problem, generator=optimize.InitialFlowsGenerator(), population_size=popsize)

		#step = 20
		#for i in range(0, 100, step):
		#	log.info("NFE: {}".format(i))
		#	self.eflows_opt.run(step)

		#	feasible = sum([1 for solution in self.eflows_opt.result if solution.feasible is True])
		#	infeasible = sum([1 for solution in self.eflows_opt.result if solution.feasible is False])
		#	log.debug("{} feasible, {} infeasible".format(feasible, infeasible))

		#	self._plot(i+step)
		self.eflows_opt.run(NFE)
		feasible = sum([1 for solution in self.eflows_opt.result if solution.feasible is True])
		infeasible = sum([1 for solution in self.eflows_opt.result if solution.feasible is False])
		log.debug("{} feasible, {} infeasible".format(feasible, infeasible))
		self._plot("Pareto Front: {} NFE, PopSize: {}".format(NFE, popsize))

		self._plot_convergence(problem.iterations, problem.objective_1, "Total Needs Satisfied v NFE")
		self._plot_convergence(problem.iterations, problem.objective_2, "Min percent of needs satisfied by species v NFE")

	def _plot(self, title):
		x = [s.objectives[0] for s in self.eflows_opt.result if s.feasible]
		y = [s.objectives[1] for s in self.eflows_opt.result if s.feasible]
		log.debug("X: {}".format(x))
		log.debug("Y: {}".format(y))
		plt.scatter(x, y)
		plt.xlim([min(x)-0.1, max(x)+0.1])
		plt.ylim([min(y)-0.1, max(y)+0.1])
		plt.xlabel("Total Needs Satisfied")
		plt.ylabel("Minimum percent of HUC needs satisfied")
		plt.title(title)
		plt.show()

	def _plot_convergence(self, i, objective, title):
		x = i
		y = objective
		plt.plot(x, y, color='steelblue', linewidth=1)
		#plt.xlim([min(x)-0.1, max(x)+0.1])
		#plt.ylim([min(y)-0.1, max(y)+0.1])
		plt.xlabel("NFE")
		plt.ylabel("Objective Value")
		plt.title(title)
		plt.show()

