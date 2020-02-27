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

	def handle(self, *args, **options):

		if options['nfe']:
			nfe = options['nfe'][0]
		else:
			nfe = 10000

		if options['model_name']:
			model_name = options['model_name'][0]
		else:
			model_name = "anderson_creek_thesis"

		if options['pop_size']:
			pop_size = options['pop_size'][0]
		else:
			pop_size = 50

		support.run_optimize_new(NFE=nfe, model_run_name=model_name, popsize=pop_size)
