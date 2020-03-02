"""
	Generates a set of figures for Nick's master's thesis.
"""

import os

from belleflopt import support  # this needs a Django shell - run python manage.py shell from belleflopt's folder, then import his script
import platypus

import logging

from django.core.management.base import BaseCommand, CommandError

log = logging.getLogger("belleflopt.commands.experimenter")


class Command(BaseCommand):
	help = 'Runs models for thesis'
	def add_arguments(self, parser):
		parser.add_argument('--algorithms', nargs='+', type=str, dest="algorithms")

	def handle(self, *args, **options):

		if "," in options["algorithms"][0]:
			algorithms = options["algorithms"][0].split(",")
			algorithms = [getattr(platypus, algorithm) for algorithm in algorithms]
		else:
			algorithms = (getattr(platypus, options["algorithms"][0]),)

		support.run_experimenter(algorithms=algorithms)
