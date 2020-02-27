import csv
import os
import logging
import random
import shelve

import numpy
import arrow
from matplotlib import pyplot as plt
from platypus import NSGAII, OMOPSO, EpsNSGAII, SMPSO, GDE3, SPEA2
import platypus

from eflows_optimization import settings
from belleflopt import models
from belleflopt import optimize
from belleflopt import comet

log = logging.getLogger("eflows.optimization.support")

NO_DOWNSTREAM = ("OCEAN", "MEXICO", "CLOSED_BASIN")


def day_of_water_year(year, month, day):
	eval_date = arrow.Arrow(year, month, day)

	if month >= 10:
		eval_year = year
	else:
		eval_year = year - 1  # if we're in Jan-Sep, the start of the water year was last year

	water_year_start = arrow.Arrow(eval_year, 10, 1)

	return (eval_date - water_year_start).days + 1  # add one because otherwise everything would be zero-indexed


def water_year(year, month):
	"""
		Given a year and a month, returns the water year
	:param year:
	:param month:
	:return:
	"""
	if month >= 10:
		return year + 1
	else:
		return year


def run_optimize_new(algorithm=NSGAII, NFE=1000, popsize=25, starting_water_price=800, economic_water_proportion = 0.99, seed=20200224, model_run_name="anderson_creek_thesis", use_comet=True, show_plots=True, run_problem=True):
	"""
		Runs a single optimization run, defaulting to 1000 NFE using NSGAII. Won't output plots to screen
		by default. Outputs tables and figures to the data/results folder.
	:param algorithm: a platypus Algorithm object (not the instance, but the actual item imported from platypus)
						defaults to NSGAII.
	:param NFE: How many times should the objective function be run?
	:param popsize: The size of hte population to use
	:param seed: Random seed to start
	:param show_plots: Whether plots should be output to the screen
	:pararm run_problem: When True, runs it, when False, just sets it up and returns it. Lets us have a consistent problem
						set up in many contexts
	:return: None
	"""

	if use_comet and run_problem:
		experiment = comet.new_experiment()
		experiment.log_parameters({"algorithm": algorithm,
	                           "NFE": NFE,
	                           "popsize": popsize,
	                           "seed": seed,
	                           "starting_water_price":starting_water_price,
	                           "economic_water_proportion": economic_water_proportion,
		                       "model_name": model_run_name
	                           })
	else:
		experiment = None

	random.seed = seed

	model_run = models.ModelRun.objects.get(name=model_run_name)

	stream_network = optimize.StreamNetwork(model_run.segments, 2010, model_run)
	problem = optimize.StreamNetworkProblem(stream_network, starting_water_price=starting_water_price, total_units_needed_factor=economic_water_proportion)

	log.info("Looking for {} CFS of water to extract".format(problem.stream_network.economic_benefit_calculator.total_units_needed))

	eflows_opt = algorithm(problem, generator=optimize.InitialFlowsGenerator(), population_size=popsize)

	if run_problem:
		eflows_opt.run(NFE)

		make_plots(eflows_opt, problem, NFE, algorithm, seed, popsize, experiment, show_plots)

		if use_comet:
			#file_path = os.path.join(settings.BASE_DIR, "data", "results", "results_{}_seed{}_nfe{}_popsize{}.csv".format(algorithm.__name__,str(seed),str(NFE),str(popsize)))
			#output_table(problem.hucs, output_path=file_path)

			#experiment.log_asset(file_path, "results.csv")
			experiment.end()

	#return file_path
	return problem


def make_plots(model_run, problem, NFE, algorithm, seed, popsize, experiment=None, show_plots=False,):
	_plot(model_run, "Pareto Front: {} NFE, PopSize: {}".format(NFE, popsize),
	      experiment=experiment,
	      show=show_plots,
	      filename=os.path.join(settings.BASE_DIR, "data", "results",
	                            "pareto_{}_seed{}_nfe{}_popsize{}.png".format(algorithm.__name__, str(seed), str(NFE),
	                                                                          str(popsize)))
	      )

	_plot_convergence(problem.iterations, problem.objective_1,
	                  "Environmental Benefit v NFE. Alg: {}, PS: {}, Seed: {}".format(algorithm.__name__, str(popsize),
	                                                                                  str(seed)),
	                  experiment=experiment,
	                  show=show_plots,
	                  filename=os.path.join(settings.BASE_DIR, "data", "results",
	                                        "convergence_obj1_{}_seed{}_nfe{}_popsize{}.png".format(algorithm.__name__,
	                                                                                                str(seed), str(NFE),
	                                                                                                str(popsize)))
	                  )

	_plot_convergence(problem.iterations, problem.objective_2,
	                  "Economic Benefit v NFE Alg: {}, PS: {}, Seed: {}".format(algorithm.__name__, str(popsize),
	                                                                            str(seed)),
	                  experiment=experiment,
	                  show=show_plots,
	                  filename=os.path.join(settings.BASE_DIR, "data", "results",
	                                        "convergence_obj2_{}_seed{}_nfe{}_popsize{}.png".format(algorithm.__name__,
	                                                                                                str(seed),
	                                                                                                str(NFE),
	                                                                                                str(popsize)))
	                  )


def run_experimenter(NFE=50000,
                     popsizes=(25, 50, 100),
                     algorithms=(NSGAII, SPEA2, SMPSO, GDE3),
                     seeds=(20200224, 19991201, 18000408, 31915071),
                     output_shelf=os.path.join(settings.BASE_DIR, "experimenter.shelf"),
                     problem_from_shelf=False,
                     resume=False):

	with shelve.open(output_shelf) as shelf:  # save the results out to a file
		if problem_from_shelf:
			problem = shelf['problem']
		else:
			problem = run_optimize_new(economic_water_proportion=0.75, use_comet=False, run_problem=False)
			shelf['problem'] = problem
			shelf.sync()

		if resume is True:
			results = shelf['results']
		else:
			results = {}

	for algorithm in algorithms:
		if type(algorithm) == tuple:  # if the algorithm has arguments, then we need to split it out so we can send them in
			algorithm_args = algorithm[1]
			algorithm = algorithm[0]
		else:
			algorithm_args = {}

		if algorithm.__name__ not in results:
			results[algorithm.__name__] = {}
		for seed in seeds:
			if seed not in results[algorithm.__name__]:
				results[algorithm.__name__][seed] = {}
			random.seed = seed
			for popsize in popsizes:
				log.info("{}, {}, {}".format(algorithm.__name__, seed, popsize))
				if popsize in results[algorithm.__name__][seed]:  # if the key already exists, it means we're resuming and this already ran
					continue

				problem.reset()
				eflows_opt = algorithm(problem, generator=optimize.InitialFlowsGenerator(), population_size=popsize, **algorithm_args)
				eflows_opt.run(NFE)

				make_plots(eflows_opt, problem, NFE, algorithm, seed, popsize, experiment=None, show_plots=False)

				results[algorithm.__name__][seed][popsize] = eflows_opt
				with shelve.open(output_shelf) as shelf:  # save the results out to a file after each round
					shelf["results"] = results

					# these will save some space in the results
					shelf["results"][algorithm.__name__][seed][popsize].problem.stream_network = None
					shelf["results"][algorithm.__name__][seed][popsize].problem.types = None
					shelf.sync()


def run_optimize(algorithm=NSGAII, NFE=1000, popsize=25, seed=20181214, show_plots=False):
	"""
		Runs a single optimization run, defaulting to 1000 NFE using NSGAII. Won't output plots to screen
		by default. Outputs tables and figures to the data/results folder.
	:param algorithm: a platypus Algorithm object (not the instance, but the actual item imported from platypus)
						defaults to NSGAII.
	:param NFE: How many times should the objective function be run?
	:param popsize: The size of hte population to use
	:param seed: Random seed to start
	:param show_plots: Whether plots should be output to the screen
	:return: None
	"""

	experiment = comet.new_experiment()
	experiment.log_parameters({"algorithm": algorithm, "NFE": NFE, "popsize": popsize, "seed": seed})

	random.seed = seed

	problem = optimize.HUCNetworkProblem()
	eflows_opt = algorithm(problem, generator=optimize.InitialFlowsGenerator(), population_size=popsize)

	#step = 20
	#for i in range(0, 100, step):
	#	log.info("NFE: {}".format(i))
	#	self.eflows_opt.run(step)

	#	feasible = sum([1 for solution in self.eflows_opt.result if solution.feasible is True])
	#	infeasible = sum([1 for solution in self.eflows_opt.result if solution.feasible is False])
	#	log.debug("{} feasible, {} infeasible".format(feasible, infeasible))

	#	self._plot(i+step)
	eflows_opt.run(NFE)
	feasible = sum([1 for solution in eflows_opt.result if solution.feasible is True])
	infeasible = sum([1 for solution in eflows_opt.result if solution.feasible is False])

	experiment.log_parameter("feasible", feasible)
	experiment.log_parameter("infeasible", infeasible)

	log.debug("{} feasible, {} infeasible".format(feasible, infeasible))
	_plot(eflows_opt, "Pareto Front: {} NFE, PopSize: {}".format(NFE, popsize),
		  				experiment=experiment,
						show=show_plots,
						filename=os.path.join(settings.BASE_DIR, "data", "results", "pareto_{}_seed{}_nfe{}_popsize{}.png".format(algorithm.__name__, str(seed), str(NFE), str(popsize))))

	_plot_convergence(problem.iterations, problem.objective_1,
					  "Total Needs Satisfied v NFE. Alg: {}, PS: {}, Seed: {}".format(algorithm.__name__, str(popsize), str(seed)),
					  	experiment=experiment,
						show=show_plots,
						filename=os.path.join(settings.BASE_DIR, "data", "results", "convergence_obj1_{}_seed{}_nfe{}_popsize{}.png".format(algorithm.__name__,str(seed),str(NFE),str(popsize))))

	_plot_convergence(problem.iterations, problem.objective_2, "Min percent of needs satisfied by species v NFEAlg: {}, PS: {}, Seed: {}".format(algorithm.__name__, str(popsize), str(seed)),
					  experiment=experiment,
					  show=show_plots,
					  filename=os.path.join(settings.BASE_DIR, "data", "results", "convergence_obj2_{}_seed{}_nfe{}_popsize{}.png".format(algorithm.__name__, str(seed),
																					   str(NFE), str(popsize))))

	for huc in problem.hucs:
		huc.save()  # save the results out

	file_path = os.path.join(settings.BASE_DIR, "data", "results", "results_{}_seed{}_nfe{}_popsize{}.csv".format(algorithm.__name__,str(seed),str(NFE),str(popsize)))
	output_table(problem.hucs, output_path=file_path)

	experiment.log_asset(file_path, "results.csv")
	experiment.end()

	return file_path


def validate_flow_methods(model_run_name="lower_navarro_thesis"):
	problem = run_optimize_new(run_problem=False, model_run_name=model_run_name)

	measurements = numpy.linspace(0, 1, 101)
	for measurement in measurements:
		log.info(measurement)
		initial_flows = optimize.SimpleInitialFlowsGenerator(measurement)

		runner = NSGAII(problem, generator=initial_flows, population_size=1)  # shouldn't matter what algorithm we use - we only do 1 NFE
		runner.run(1)  # run it for 1 NFE just to see what these initial flows do

	_plot_convergence(problem.iterations, problem.objective_1,
	                  "Environmental benefit w/percent of flows: {}".format(model_run_name),
	                  experiment=None,
	                  show=True,
	                  filename=os.path.join(settings.BASE_DIR, "data", "results","validation_plot.png"))




def _plot(optimizer, title, experiment=None, filename=None, show=False):
	x = [s.objectives[0] for s in optimizer.result]
	y = [s.objectives[1] for s in optimizer.result]

	if experiment is not None:
		comet.log_metric("EnvironmentalBenefit", x, experiment=experiment)  # log the resulting values
		comet.log_metric("EconomicBenefit", y, experiment=experiment)

	log.debug("X: {}".format(x))
	log.debug("Y: {}".format(y))
	plt.scatter(x, y)
	plt.xlabel("Environmental Flow Benefit")
	plt.ylabel("Economic Benefit")
	plt.title(title)

	if experiment is not None:
		experiment.log_figure(title)

	if filename:
		plt.savefig(fname=filename)
	if show:
		plt.show()

	plt.close()


def _plot_convergence(i, objective, title, experiment=None, filename=None, show=False):
	x = i
	y = objective
	plt.plot(x, y, color='steelblue', linewidth=1)
	#plt.xlim([min(x)-0.1, max(x)+0.1])
	#plt.ylim([min(y)-0.1, max(y)+0.1])
	plt.xlabel("NFE")
	plt.ylabel("Objective Value")
	plt.title(title)

	if experiment:
		experiment.log_figure(title)

	if filename:
		plt.savefig(fname=filename)
	if show:
		plt.show()

	plt.close()


def output_table(hucs, output_path=os.path.join(settings.BASE_DIR, "data", "results.csv")):
	outputs = []
	for huc in hucs:
		output = {}
		output["HUC_12"] = huc.huc_id
		output["initial_available"] = huc.initial_available_water
		output["allocation"] = huc.flow_allocation
		assemblage = huc.assemblage.all()
		output["assemblage"] = ", ".join([species.common_name for species in assemblage])
		unmet_needs = []
		for species in assemblage:
			species_min_need = models.SpeciesComponent.objects.get(species=species, component__name="min_flow").value
			if species_min_need > huc.flow_allocation:
				if huc.flow_allocation == 0:
					pct = "No Flow"
				else:
					pct = round((species_min_need / huc.flow_allocation) * 100)
				unmet_needs.append("{} ({}%)".format(species.common_name, pct))
		output["unmet_needs"] = ", ".join(unmet_needs)
		output["unmet_count"] = len(unmet_needs)
		output["richness"] = huc.assemblage.count()
		output["unmet_proportion"] = output["unmet_count"] / output["richness"]

		outputs.append(output)

	fields = ["HUC_12", "initial_available", "allocation", "assemblage", "unmet_needs",
			  	"unmet_count", "richness", "unmet_proportion" ]

	with open(output_path, 'w', newline="\n") as output_file:
		writer = csv.DictWriter(output_file, fieldnames=fields)
		writer.writeheader()
		writer.writerows(outputs)


def run_optimize_many():
	"""
		Runs through many algorithms and many seeds - outputs results for all
	:return:
	"""

	algorithms = [NSGAII, SMPSO, SPEA2, GDE3]
	nfe = 800
	popsize = [25, 50, 100]
	seeds = [20181214, 236598, 12958]
	for algorithm in algorithms:
		for pop in popsize:
			for seed in seeds:
				run_optimize(algorithm, NFE=nfe, popsize=pop, seed=seed)


def _segment_plot_helper(function, segment_id, component_id, screen, output_path, **kwargs):
	"""
		A helper function handle plotting
	:param function: a method on a benefit object that handles plotting and takes a parameter "screen" and "output_path"
	                along with any other params
	:param segment_id: An NHDPlus COMID
	:param component_id: A CEFF Flow Component ID
	:param screen: when True, displays the plot on the screen
	:param output_path: When specified, saves the plot to this location
	:param kwargs: Any other keyword arguments to pass to the benefit object plotting function
	:return: None - plots and/or saves figure as specified
	"""
	segment_component = models.SegmentComponent.objects.get(component__ceff_id=component_id,
	                                                        stream_segment__com_id=segment_id)
	segment_component.make_benefit()

	function_to_call = getattr(segment_component.benefit, function)
	plot = function_to_call(screen=screen, **kwargs)

	if output_path is not None:
		plot = plot.get_figure()  # for newer seaborn, we have to get the figure from the subplot
		plot.savefig(output_path)

	plt.close()


def plot_segment_component_annual_benefit(segment_id, component_id, screen=True, output_path=None):
	"""
		A helper function that is itself its own form of documentation of setup process.
		Retrieves the flow component data for a segment and plots the annual benefit
		surface.

	:param segment_id: An NHDPlus COMID
	:param component_id: A CEFF Flow Component ID
	:param screen: when True, displays the plot on the screen
	:param output_path: When specified, saves the plot to this location
	:return: None - plots to screen and/or file as specified and closes plot
	"""

	_segment_plot_helper(function="plot_annual_benefit",
	                            segment_id=segment_id,
	                            component_id=component_id,
	                            screen=screen,
	                            output_path=output_path)


def plot_segment_component_day_benefit(segment_id, component_id, day=100, screen=True, output_path=None):
	"""
		A helper function that is itself its own form of documentation of setup process.
		Retrieves the flow component data for a segment and plots the flow benefit for a single
		day of the water year

	:param segment_id: An NHDPlus COMID
	:param component_id: A CEFF Flow Component ID
	:param day: the day of year to make the plot for
	:param screen: when True, displays the plot on the screen
	:param output_path: When specified, saves the plot to this location
	:return: None - plots to screen and/or file as specified and closes plot
	"""

	_segment_plot_helper(function="plot_flow_benefit",
	                            segment_id=segment_id,
	                            component_id=component_id,
	                            screen=screen,
	                            output_path=output_path,
								day_of_year=day)


