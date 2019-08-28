import logging

from django.test import TestCase

from belleflopt import benefit

log = logging.getLogger("belleflopt.tests")


class TestBenefitPlots(TestCase):
    def setUp(self):
        self.bb = benefit.BenefitBox()
        self.bb.low_flow = 200
        self.bb.high_flow = 400
        self.bb.start_day_of_water_year = 0
        self.bb.end_day_of_water_year = 365
    
    def test_q_values(self):
        # at the bounds, benefit is 50%
        self.assertAlmostEqual(self.bb.single_flow_benefit(200, flow_day=100), 0.5)
        self.assertAlmostEqual(self.bb.single_flow_benefit(400, flow_day=100), 0.5)
        
        # get a little bit in-between to make sure the slope is OK
        self.assertAlmostEqual(self.bb.single_flow_benefit(190, flow_day=100), 0.25)
        self.assertAlmostEqual(self.bb.single_flow_benefit(210, flow_day=100), 0.75)
        self.assertAlmostEqual(self.bb.single_flow_benefit(390, flow_day=100), 0.75)
        self.assertAlmostEqual(self.bb.single_flow_benefit(410, flow_day=100), 0.25)
        
        # test qs at the boundaries where the slope hits x axis
        self.assertEqual(self.bb.single_flow_benefit(420, flow_day=100), 0)
        self.assertEqual(self.bb.single_flow_benefit(180, flow_day=100), 0)
        
        # test qs where the they should hit 1 and start descending from 1
        self.assertEqual(self.bb.single_flow_benefit(220, flow_day=100), 1)
        self.assertEqual(self.bb.single_flow_benefit(380, flow_day=100), 1)
    
    def plot(self):
        self.bb.plot_benefit()