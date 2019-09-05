import logging

from django.test import TestCase

from belleflopt import benefit

log = logging.getLogger("belleflopt.tests")


class TestBenefitPlots(TestCase):
    def setUp(self):
        self.bb = benefit.BenefitBox(low_flow=200, high_flow=400, start_day_of_water_year=0, end_day_of_water_year=365)

    def test_flow_benefit_values(self):
        """
            Just a simple test - we might want to make some tests that have different values,
            and we'll definitely want some that handle the dates with date slopes and the 
            interactions between date slopes and flow slopes
        """
        # at the bounds, benefit is 50%
        self.assertAlmostEqual(self.bb.single_flow_benefit(200, day_of_year=100), 0.5)
        self.assertAlmostEqual(self.bb.single_flow_benefit(400, day_of_year=100), 0.5)
        
        # get a little bit in-between to make sure the slope is OK
        self.assertAlmostEqual(self.bb.single_flow_benefit(190, day_of_year=100), 0.25)
        self.assertAlmostEqual(self.bb.single_flow_benefit(210, day_of_year=100), 0.75)
        self.assertAlmostEqual(self.bb.single_flow_benefit(390, day_of_year=100), 0.75)
        self.assertAlmostEqual(self.bb.single_flow_benefit(410, day_of_year=100), 0.25)
        
        # test qs at the boundaries where the slope hits x axis
        self.assertEqual(self.bb.single_flow_benefit(420, day_of_year=100), 0)
        self.assertEqual(self.bb.single_flow_benefit(180, day_of_year=100), 0)
        
        # test qs where the they should hit 1 and start descending from 1
        self.assertEqual(self.bb.single_flow_benefit(220, day_of_year=100), 1)
        self.assertEqual(self.bb.single_flow_benefit(380, day_of_year=100), 1)
        self.plot()

    def plot(self):
        self.bb.plot_flow_benefit()


class TestQValues(TestCase):
    def test_q_calculation_with_margin(self):
        """
            Tests that the q values get put in the correct place with a standard margin of 0.1
        :return:
        """
        bb = benefit.BenefitBox(low_flow=200, high_flow=400, start_day_of_water_year=0, end_day_of_water_year=365, flow_margin=0.1)
        self.assertAlmostEqual(bb.flow_item._q1, 180)
        self.assertAlmostEqual(bb.flow_item._q2, 220)
        self.assertAlmostEqual(bb.flow_item._q3, 380)
        self.assertAlmostEqual(bb.flow_item._q4, 420)

    def test_date_q_values_at_boundaries(self):
        """
            This test makes sure that when we have date values at the boundaries of water years, we don't slope the
            benefit function
        :return:
        """
        bb = benefit.BenefitBox(low_flow=200, high_flow=400, start_day_of_water_year=0, end_day_of_water_year=365,
                                flow_margin=0.1)
        self.assertEqual(bb.date_item._q1, bb.date_item._q2)
        self.assertEqual(bb.date_item._q1, 0)
        self.assertEqual(bb.date_item._q3, bb.date_item._q4)
        self.assertEqual(bb.date_item._q3, 365)


class TestCrossYearComponent(TestCase):
    """
        Tests for flow components that cross water years
    """

    def test_simple_cross_year_component(self):
        self.assertRaises(NotImplementedError, benefit.BenefitBox,
                          low_flow=200,
                          high_flow=400,
                          start_day_of_water_year=300,
                          end_day_of_water_year=50,
                          date_margin=0.2)
