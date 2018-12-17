# Eflows Optimization

A tool to allocate unimpaired flows optimally for environmental purposes.

Developed for Python 3.6 and Django 2.1.

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
In the shell, run the following to load species, watershed, and flow data and set up the
hydrologic network
```python
from eflows import support
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

If you want to do some testing, you can use `support.run_optimize_many()` (takes no arguments
 - tweak the code if you want it to be different) or use Platypus' Experimenter class.
 Note that currently, due to the way the model is constructed, you can't use parallel
 expirementers - the database will lock and prevent multiple accesses.
 
 ## Performance
 This model is slow right now, sorry. It's built into Django, which makes data management
 and network traversal nice, but also slows everything down and prevents parallelization
 while using a SQLite backend. One function evaluation takes about a second or more on
 modest hardware, so plan accordingly. Most runs converged in less than 4000 NFE, but
 it's possible you'd want to go further for testing.