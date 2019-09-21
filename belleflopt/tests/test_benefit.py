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
        #self.plot()

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
        bb = benefit.BenefitBox(low_flow=200,
                          high_flow=400,
                          start_day_of_water_year=200,
                          end_day_of_water_year=50,
                            component_name="test crossyear component"
                        )
        # bb.plot_annual_benefit()  - was just for visualizing the box we set up for testing
        # at flows of 180 and 420, these will always have 0 benefit
        for day in range(0, 366):
            self.assertEqual(bb.single_flow_benefit(420, day_of_year=day), 0)
            self.assertEqual(bb.single_flow_benefit(180, day_of_year=day), 0)

        # on these days, any flow should be 0 benefit
        for flow in range(0, 450):
            self.assertEqual(bb.single_flow_benefit(flow, day_of_year=70), 0)
            self.assertEqual(bb.single_flow_benefit(flow, day_of_year=180), 0)

        self.assertEqual(bb.single_flow_benefit(300, day_of_year=25), 1)  # a random set of values within the bulk of
        self.assertEqual(bb.single_flow_benefit(350, day_of_year=250), 1)  # the area of full benefit
        self.assertEqual(bb.single_flow_benefit(375, day_of_year=300), 1)
        self.assertEqual(bb.single_flow_benefit(250, day_of_year=365), 1)

        edge_value = bb.single_flow_benefit(250, day_of_year=200)  # get test values in the fuzzy margins
        edge_value2 = bb.single_flow_benefit(200, day_of_year=200)
        edge_value3 = bb.single_flow_benefit(200, day_of_year=300)

        self.assertLess(edge_value, 1)  # fuzzy left edge
        self.assertLess(edge_value2, 1)  # fuzzy corner
        self.assertLess(edge_value3, 1)  # fuzzy bottom edge
        self.assertGreater(edge_value, 0)
        self.assertGreater(edge_value2, 0)
        self.assertGreater(edge_value3, 0)
        # self.assertEqual()
