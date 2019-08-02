import os

import comet_ml


def new_experiment():
	return comet_ml.Experiment(
		project_name="belleflopt",
		workspace="nickrsan",
		api_key=os.environ["COMET_ML_API_KEY"]
	)
