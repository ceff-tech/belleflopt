"""
	Generates a set of figures for Nick's master's thesis.
"""

import os

from belleflopt import support  # this needs a Django shell - run python manage.py shell from belleflopt's folder, then import his script

import logging

from django.core.management.base import BaseCommand, CommandError

log = logging.getLogger("belleflopt.commands.run_models")


class Command(BaseCommand):
	help = 'Runs model for thesis'

	def add_arguments(self, parser):
		parser.add_argument('--nfe', nargs='+', type=int, dest="nfe", default=10000,)
		parser.add_argument('--model_name', nargs='+', type=str, dest="model_name", default="anderson_creek_thesis",)
		parser.add_argument('--pop_size', nargs='+', type=int, dest="pop_size", default="50",)
		parser.add_argument('--use_comet', nargs='+', type=int, dest="use_comet", default=0,)
		parser.add_argument('--min_proportion', nargs='+', type=float, dest="min_proportion", default=0,)
		parser.add_argument('--checkpoint_interval', nargs='+', type=int, dest="checkpoint_interval", default=None,)

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

		support.run_optimize_new(**kwargs)

