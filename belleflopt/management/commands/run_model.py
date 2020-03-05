"""
	Generates a set of figures for Nick's master's thesis.
"""

import os

from belleflopt import support  # this needs a Django shell - run python manage.py shell from belleflopt's folder, then import his script

import logging

import platypus

from django.core.management.base import BaseCommand, CommandError

log = logging.getLogger("belleflopt.commands.run_models")


class Command(BaseCommand):
	help = 'Runs model for thesis'

	def add_arguments(self, parser):
		parser.add_argument('--nfe', nargs='+', type=int, dest="nfe")
		parser.add_argument('--model_name', nargs='+', type=str, dest="model_name")
		parser.add_argument('--pop_size', nargs='+', type=int, dest="pop_size")
		parser.add_argument('--use_comet', nargs='+', type=int, dest="use_comet")
		parser.add_argument('--min_proportion', nargs='+', type=float, dest="min_proportion")
		parser.add_argument('--checkpoint_interval', nargs='+', type=int, dest="checkpoint_interval")
		parser.add_argument('--algorithm', nargs='+', type=str, dest="algorithm")
		parser.add_argument('--simplified', nargs='+', type=int, dest="simplified")
		parser.add_argument('--plot_all', nargs='+', type=int, dest="plot_all")

	def handle(self, *args, **options):

		kwargs = {}

		# could probably shorten the rest of this (except the comet line) to a dict comprehension, but this is pretty readable
		if options['nfe']:
			kwargs["NFE"] = options['nfe'][0]

		if options['model_name']:
			kwargs["model_run_name"] = options['model_name'][0]

		if options['pop_size']:
			kwargs["popsize"] = options['pop_size'][0]

		if options['use_comet']:
			kwargs["use_comet"] = int(options['use_comet'][0]) == 1

		if options['min_proportion']:
			kwargs["min_proportion"] = options['min_proportion'][0]

		if options['checkpoint_interval']:
			kwargs["checkpoint_interval"] = options['checkpoint_interval'][0]

		if options['algorithm']:
			kwargs["algorithm"] = getattr(platypus, options['algorithm'])

		if options['simplified']:
			kwargs["simplified"] = int(options['simplified'][0]) == 1
			
		if options['plot_all']:
			kwargs["plot_all"] = int(options['plot_all'][0]) == 1

		support.run_optimize_new(**kwargs)

