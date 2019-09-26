"""
	Generates a set of figures for Nick's master's thesis.
"""

import os

from belleflopt import support  # this needs a Django shell - run python manage.py shell from belleflopt's folder, then import his script

import logging

from django.core.management.base import BaseCommand, CommandError

log = logging.getLogger("belleflopt.commands.generate_figures")


class Command(BaseCommand):
	help = 'Generates figures for Nick\'s master\'s thesis.'

	def add_arguments(self, parser):
		parser.add_argument('--output_folder', nargs='+', type=str, dest="output_folder", default=False,)

	def handle(self, *args, **options):

		if options['output_folder']:
			output_folder = options['output_folder'][0]
		else:
			output_folder = r"C:\Users\dsx\Dropbox\Graduate\Thesis\figures"

		support.plot_segment_component_annual_benefit("14992951", "Wet_BFL", screen=False, output_path=os.path.join(output_folder, "14992951_Wet_annual.png"))
		support.plot_segment_component_day_benefit("14992951", "Wet_BFL", day=100, screen=False, output_path=os.path.join(output_folder, "14992951_Wet_day100.png"))
		support.plot_segment_component_annual_benefit("14992951", "DS", screen=False, output_path=os.path.join(output_folder, "14992951_DS_annual.png"))
		support.plot_segment_component_day_benefit("14992951", "DS", day=100, screen=False, output_path=os.path.join(output_folder, "14992951_DS_day100.png"))
		support.plot_segment_component_annual_benefit("8058675", "Wet_BFL", screen=False, output_path=os.path.join(output_folder, "8058675_Wet_annual.png"))
		support.plot_segment_component_day_benefit("8058675", "Wet_BFL", day=100, screen=False, output_path=os.path.join(output_folder, "8058675_Wet_day100.png"))
		support.plot_segment_component_annual_benefit("8058675", "DS", screen=False, output_path=os.path.join(output_folder, "8058675_DS_annual.png"))
		support.plot_segment_component_day_benefit("8058675", "DS", day=100, screen=False, output_path=os.path.join(output_folder, "8058675_DS_day100.png"))
