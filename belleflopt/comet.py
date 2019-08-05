import os

import comet_ml


def new_experiment():
	return comet_ml.Experiment(
		project_name="belleflopt",
		workspace="nickrsan",
		api_key=os.environ["COMET_ML_API_KEY"]
	)


def log_metric(name, values, experiment):
	"""
		Comet tracks metrics as values with a step, so this translates lists
		into values that have a step
	:param name: a name to assign the list on Comet.ML
	:param values: a Python list
	:param experiment: An open Comet.ml Experiment object
	:return:
	"""

	for i, value in enumerate(values):
		experiment.log_metric(name=name, value=value, step=i)
