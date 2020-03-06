import csv
import os
import logging
import random
import shelve

import numpy
import arrow
import matplotlib as mpl
from matplotlib import pyplot as plt
from platypus import NSGAII, OMOPSO, EpsNSGAII, SMPSO, GDE3, SPEA2, nondominated

from eflows_optimization import settings
from belleflopt import models
from belleflopt import optimize
from belleflopt import comet

log = logging.getLogger("eflows.optimization.support")

NO_DOWNSTREAM = ("OCEAN", "MEXICO", "CLOSED_BASIN")

# See https://github.com/matplotlib/matplotlib/issues/5907 - solves an issue with plotting *lots* of points on a figure
mpl.rcParams['agg.path.chunksize'] = 10000


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


def run_optimize_new(algorithm=NSGAII,
                     NFE=1000,
                     popsize=25,
                     starting_water_price=800,
                     economic_water_proportion = 0.99,
                     seed=20200224,
                     model_run_name="upper_cosumnes_subset_2010",
                     use_comet=True,
                     show_plots=True,
                     run_problem=True,
                     min_proportion=0,
                     checkpoint_interval=True,
                     simplified=False,
                     plot_all=False):
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
	:param min_proportion: What is the minimum proportion of flow that we can allocate to any single segment? Raising
			this value (min 0, max 0.999999999) prevents the model from extracting all its water in one spot.
	:param checkpoint_interval: How many NFE should elapse before this writes out plots and shelf results. Then writes
			those out every NFE interval until more than NFE. If True instead of a number, then defaults to int(NFE/10).
			If NFE is not evenly divisible by checkpoint_interval, then runs to the largest multiple of checkpoint_interval
			less than NFE.
	:param plot_all: Makes a hydrograph/component plot for every segment and population member in the final solution set.
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
		                       "model_name": model_run_name,
		                        "min_eflows_proportion": min_proportion,
	                           })
	else:
		experiment = None

	random.seed = seed

	model_run = models.ModelRun.objects.get(name=model_run_name)

	stream_network = optimize.StreamNetwork(model_run.segments, model_run.water_year, model_run)
	problem = optimize.StreamNetworkProblem(stream_network,
	                                        starting_water_price=starting_water_price,
	                                        total_units_needed_factor=economic_water_proportion,
	                                        min_proportion=min_proportion,
	                                        simplified=simplified)

	log.info("Looking for {} CFS of water to extract".format(problem.stream_network.economic_benefit_calculator.total_units_needed))

	eflows_opt = algorithm(problem, generator=optimize.InitialFlowsGenerator(), population_size=popsize)

	if run_problem:
		elapsed_nfe = 0
		if checkpoint_interval is True:
			if NFE > 1000:
				checkpoint_interval = int(NFE/10)
			else:
				checkpoint_interval = int(NFE/2)
		if checkpoint_interval is False or checkpoint_interval is None:
			checkpoint_interval = NFE

		# TODO: This construction means the comet.ml metric logging is duplicated, but whatever right now.
		for total_nfe in range(checkpoint_interval, NFE+1, checkpoint_interval):
			eflows_opt.run(checkpoint_interval)

			make_plots(eflows_opt, problem, total_nfe, algorithm, seed, popsize, model_run_name, experiment, show_plots, plot_all=plot_all, simplified=simplified)

		log.info("Completed at {}".format(arrow.utcnow()))
		if use_comet:
			#file_path = os.path.join(settings.BASE_DIR, "data", "results", "results_{}_seed{}_nfe{}_popsize{}.csv".format(algorithm.__name__,str(seed),str(NFE),str(popsize)))
			#output_table(problem.hucs, output_path=file_path)

			#experiment.log_asset(file_path, "results.csv")
			experiment.end()

	#return file_path
	return {"problem": problem, "solution": eflows_opt}


def incremental_maximums(values, seed=0):
	"""
		Generator that keeps track of our max value we've seen so we can simplify convergence plots to only the
		increasing values
	:param values:
	:param seed:
	:return:
	"""
	for value in values:
		if value > seed:
			seed = value
			yield value


def get_best_items_for_convergence(objective_values):
	return list(incremental_maximums(objective_values))  # get the actual sequential max list


def write_variables_as_shelf(model_run, output_folder):
	log.info("Writing out variables and objectives to shelf")
	results = nondominated(model_run.result)
	variables = [s.variables for s in results]
	objectives = [s.objectives for s in results]
	with shelve.open(os.path.join(output_folder, "variables.shelf")) as shelf:
		shelf["variables"] = variables
		shelf["objectives"] = objectives
		shelf["result"] = model_run.result
		shelf.sync()


def plot_all_solutions(solution, problem, simplified, segment_name, output_folder, show_plots):

	for i, solution in enumerate(nondominated(solution.result)):
		problem.stream_network.set_segment_allocations(solution.variables, simplified=simplified)
		for segment in problem.stream_network.stream_segments.values():
			output_segment_name = "{}_sol_{}".format(segment_name, i)
			segment.plot_results_with_components(screen=show_plots, output_folder=output_folder, name_prefix=output_segment_name)


def replot_from_shelf():
	pass


def make_plots(model_run, problem, NFE, algorithm, seed, popsize, name, experiment=None, show_plots=False, plot_all=False, simplified=False):
	output_folder = os.path.join(settings.BASE_DIR, "data", "results", name, str(NFE), algorithm.__name__, str(seed), str(popsize))
	os.makedirs(output_folder, exist_ok=True)

	write_variables_as_shelf(model_run, output_folder)

	_plot(model_run, "Pareto Front: {} NFE, PopSize: {}".format(NFE, popsize),
	      experiment=experiment,
	      show=show_plots,
	      filename=os.path.join(output_folder,
	                            "pareto_{}_seed{}_nfe{}_popsize{}.png".format(algorithm.__name__, str(seed), str(NFE),
	                                                                          str(popsize)))
	      )

	try:
		_plot_convergence(problem.iterations, problem.objective_1,
		                  "Environmental Benefit v NFE. Alg: {}, PS: {}, Seed: {}".format(algorithm.__name__, str(popsize),
		                                                                                  str(seed)),
		                  experiment=experiment,
		                  show=show_plots,
		                  filename=os.path.join(output_folder,
		                                        "convergence_obj1_{}_seed{}_nfe{}_popsize{}.png".format(algorithm.__name__,
		                                                                                                str(seed), str(NFE),
		                                                                                                str(popsize)))
		                  )

		_plot_convergence(problem.iterations, problem.objective_2,
		                  "Economic Benefit v NFE Alg: {}, PS: {}, Seed: {}".format(algorithm.__name__, str(popsize),
		                                                                            str(seed)),
		                  experiment=experiment,
		                  show=show_plots,
		                  filename=os.path.join(output_folder,
		                                        "convergence_obj2_{}_seed{}_nfe{}_popsize{}.png".format(algorithm.__name__,
		                                                                                                str(seed),
		                                                                                                str(NFE),
		                                                                                                str(popsize)))
		                  )
	except OverflowError:
		log.error("Couldn't outplot convergence plot - too many points. Continuing anyway, but you may wish to stop"
		          "this run if it's not outputting convergence plots anymore!")


	segment_name = "scplot_m{}_{}_s{}_nfe{}_ps{}".format(name, algorithm.__name__,
	                                                                            str(seed),
	                                                                            str(NFE),
	                                                                            str(popsize))
	
	if plot_all:
		plot_all_solutions(solution=model_run,
		                   problem=problem,
		                   simplified=simplified,
		                   segment_name=segment_name,
		                   output_folder=output_folder,
		                   show_plots=show_plots)
	else:
		# just plot the last one done - not necessarily the most optimal in *any* sense
		for segment in problem.stream_network.stream_segments.values():
			segment.plot_results_with_components(screen=show_plots, output_folder=output_folder, name_prefix=segment_name)


def run_experimenter(NFE=50000,
                     popsizes=(100, 50),
                     algorithms=(NSGAII, SPEA2, SMPSO, GDE3),
                     seeds=(19991201, 18000408, 31915071, 20200224),
                     output_shelf=None,
                     problem_from_shelf=False,
                     resume=False,
                     model_run_names=("upper_cosumnes_subset_2010", "upper_cosumnes_subset_2011"),
                     starting_water_price=800,
                     economic_water_proportion=0.8, ):

	# results = {}

	for model_run_name in model_run_names:

		problem = run_optimize_new(model_run_name=model_run_name,
		                           starting_water_price=starting_water_price,
		                           economic_water_proportion=economic_water_proportion,
		                           use_comet=False,
		                           run_problem=False)["problem"]

		for algorithm in algorithms:
			if type(algorithm) == tuple:  # if the algorithm has arguments, then we need to split it out so we can send them in
				algorithm_args = algorithm[1]
				algorithm = algorithm[0]
			else:
				algorithm_args = {}

			#if algorithm.__name__ not in results:
				#results[algorithm.__name__] = {}
			for seed in seeds:
				#if seed not in results[algorithm.__name__]:
					#results[algorithm.__name__][seed] = {}
				random.seed = seed
				for popsize in popsizes:
					log.info("{}, {}, {}".format(algorithm.__name__, seed, popsize))
					#if popsize in results[algorithm.__name__][seed]:  # if the key already exists, it means we're resuming and this already ran
					#	continue

					experiment = comet.new_experiment()
					experiment.log_parameters({"algorithm": algorithm,
					                           "NFE": NFE,
					                           "popsize": popsize,
					                           "seed": seed,
					                           "starting_water_price": starting_water_price,
					                           "economic_water_proportion": economic_water_proportion,
					                           "model_name": model_run_name
					                           })

					problem.reset()
					eflows_opt = algorithm(problem, generator=optimize.InitialFlowsGenerator(), population_size=popsize, **algorithm_args)
					eflows_opt.run(NFE)

					make_plots(eflows_opt, problem, NFE, algorithm, seed, popsize, model_run_name, experiment=experiment, show_plots=False)

					#results[algorithm.__name__][seed][popsize] = eflows_opt
					#with shelve.open(output_shelf) as shelf:  # save the results out to a file after each round
					#	shelf["results"] = results

						# these will save some space in the results
					#	shelf["results"][algorithm.__name__][seed][popsize].problem.stream_network = None
					#	shelf["results"][algorithm.__name__][seed][popsize].problem.types = None
					#	shelf.sync()

					experiment.end()



def validate_flow_methods(model_run_name="upper_cosumnes_subset_2010", show_plot=True):
	problem = run_optimize_new(run_problem=False, model_run_name=model_run_name)["problem"]

	measurements = numpy.linspace(0, 1, 101)
	for measurement in measurements:
		log.info(measurement)
		initial_flows = optimize.SimpleInitialFlowsGenerator(measurement)

		runner = NSGAII(problem, generator=initial_flows, population_size=1)  # shouldn't matter what algorithm we use - we only do 1 NFE
		runner.run(1)  # run it for 1 NFE just to see what these initial flows do

	plt.plot(problem.iterations, problem.objective_1)

	plt.xlabel("Proportion of Available Flow")
	plt.ylabel("Environmental Benefit")

	plt.savefig(os.path.join(settings.BASE_DIR, "data", "results", "validation_plot_{}.png".format(model_run_name)), dpi=300)

	if show_plot:
		plt.show()

	plt.close()

	return {"x": problem.iterations, "y": problem.objective_1}


def validation_plot_thesis(show_plot=True, results_2010=None, results_2011=None):
	"""
		Hardcoded items because they're for my thesis, not meant for more general use.
	:return:
	"""
	if results_2010 is None:
		results_2010 = validate_flow_methods("upper_cosumnes_subset_2010", show_plot=False)
	if results_2011 is None:
		results_2011 = validate_flow_methods("upper_cosumnes_subset_2011", show_plot=False)

	# Creates two subplots and unpacks the output array immediately

	fig = plt.figure()
	plt.margins(0)
	full_plot = fig.add_subplot(1, 1, 1)  # The big subplot

	full_plot.set_xlabel("Percent of Available Flow")
	full_plot.set_ylabel("Environmental Benefit", labelpad=20)  # move it off the tick values

	# Turn off axis lines and ticks of the big subplot
	full_plot.spines['top'].set_color('none')
	full_plot.spines['bottom'].set_color('none')
	full_plot.spines['left'].set_color('none')
	full_plot.spines['right'].set_color('none')
	full_plot.tick_params(labelcolor='w', top=False, bottom=False, left=False, right=False)

	left_plot = fig.add_subplot(1, 2, 1)  # The big subplot
	left_plot.plot(results_2010["x"], results_2010["y"])
	left_plot.set_title('2010')

	right_plot = fig.add_subplot(1, 2, 2, sharey=left_plot)  # The big subplot
	right_plot.plot(results_2011["x"], results_2011["y"])
	right_plot.set_title('2011')

	# remove the axis values on the left to make space
	right_plot.tick_params(left=True, labelleft=False, )

	plt.savefig(os.path.join(settings.BASE_DIR, "data", "results", "validation_plot_thesis.png"), dpi=300)

	if show_plot:
		plt.show()

	plt.close()

	return results_2010, results_2011


def _plot(optimizer, title, experiment=None, filename=None, show=False):
	results = nondominated(optimizer.result)
	x = [s.objectives[0] for s in results]
	y = [s.objectives[1] for s in results]

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
		plt.savefig(fname=filename, dpi=300)
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
		plt.savefig(fname=filename, dpi=300)
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
		plot.savefig(output_path, dpi=300)

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


