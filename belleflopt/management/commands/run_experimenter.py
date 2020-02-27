"""
	Generates a set of figures for Nick's master's thesis.
"""

import os

from belleflopt import support  # this needs a Django shell - run python manage.py shell from belleflopt's folder, then import his script

import logging

from django.core.management.base import BaseCommand, CommandError

log = logging.getLogger("belleflopt.commands.experimenter")


class Command(BaseCommand):
	help = 'Runs models for thesis'

	def handle(self, *args, **options):

		support.run_experimenter()
