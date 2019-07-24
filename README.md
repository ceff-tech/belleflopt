# Belleflopt - An Environmental Flows Optimization Platform
A tool to allocate unimpaired flows optimally for environmental purposes. Developed for Python 3.6 and Django 2.1.

## What's with the name?
It's prounounced like "belly flopped", and can be broken down as:
* _bell_ - just a support for the rest of it
* _e_ - "environment"
* _flo_ - "flow"
* _opt_ - "optimization"

And belly flops are a silly thing that happens in water sometimes. This codebase uses an
evolutionary algorithm to find optimal environmental flow and economic tradeoffs,
so it might perform a few bellyflops of its own.

## Setup
To use, first rename `eflows_optimization/local_settings_template.py` to
`eflows_optimization/local_settings.py`. Inside that file, change the value
of `SECRET_KEY` to a cryptographically secure value.

Next, install dependencies:
```
python -m pip install -r requirements.txt
```

Then set up the database. First, create it,

```
python manage.py migrate
python manage.py shell 
```

## Running the prototype
In the shell, run the following to load species, watershed, and flow data and set up the
hydrologic network
```python
from belleflopt import support
support.reset()
```

If you want to actually run optimization now, you can then:
```python
support.run_optimize()
```

That function's signature looks like the following:
```
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
```

If you want to take a look at the optimization innards, they're in
`eflows.optimize` as a subclass of Platypus's `Problem` class.

Currently, there is no web component to this project, despite being
developed in Django. That's just futureproofing - it's all console
access now. Unittests are available for data loading functions, but
not for other functionality.

If you want to do some testing, you can use `support.run_optimize_many()` (takes no
arguments - tweak the code if you want it to be different) or use Platypus' Experimenter class.
Note that currently, due to the way the model is constructed, you can't use parallel
expirementers - the database will lock and prevent multiple accesses.

## Plugins
The codebase is being designed to utilize a plugin infrastructure that encompasses as much as
possible, to allow for this code to be a research platform that encourages exploration of outcomes
as opposed to something that runs once and gives an answer. Plugins live in the `eflows.plugins` package
and can be a package or a single module. If you create a package, the entry point must live in the `__init__.py`
file so it can be found.

Plugins are broadly split into two subfolders: `economics` and `environment` - each being
used for objective functions that evaluate economic and environmental benefits of specific flows.

In the future, it is possible that results and visualization may be included in plugins as well.

To access a plugin from code, use `eflows.plugins.return_plugin_function`. For example, to get
the entry point `environmental_benefit` from the `base` plugin in the `environment` folder, use
the following:
```python
    from eflows import plugins
    
    environmental_benefit = plugins.return_plugin_function(package="eflows.plugins.environment.base", entry_point="environmental_benefit")
```

## Model Runs
Model runs are handled in unit tests. While the main `eflows.tests` package holds standard
unit tests, the `eflows.tests.model_runs` package is special in that each test class in a file
in that package describes a discrete model run. Upon each commit, these runs will be re-evaluated
with results uploaded to comet.ml so that performance of the results can be tracked over time,
even as the code changes, allowing us to see if a model run that previously performed poorly is
better after certain bugfixes, etc.

The actual utilization of the model_runs package is not yet determined, but will be included here.
 
## Results
Sample results are included below:
![Sample Results](maps/maps_layout.png)

## Performance
This model is slow right now, sorry. It's built into Django, which makes data management
and network traversal nice, but also slows everything down and prevents parallelization
while using a SQLite backend. One function evaluation takes about a second or more on
modest hardware, so plan accordingly. Most runs converged in less than 4000 NFE, but
it's possible you'd want to go further for testing.