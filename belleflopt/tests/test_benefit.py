import logging

from django.test import TestCase

from belleflopt import benefit

log = logging.getLogger("belleflopt.tests")


class TestBenefitPlots(TestCase):
    def test_plot(self):
        bb = benefit.BenefitBox()
        bb.low_flow = 200
        bb.high_flow = 400
        bb.start_day_of_water_year = 0
        bb.end_day_of_water_year = 365
        bb.plot_benefit()