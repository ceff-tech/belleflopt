import logging

from django.test import TestCase

from eflows import support

log = logging.getLogger("eflows.optimization.tests")


class TestOptimization(TestCase):
	"""
		This test was the initial test we used to run the prototype.
		It is likely obsolete and will be replaced by a test per configuration
		that runs the optimization and logs results to comet.ml
	"""
	def setUp(self):
		support.reset()  # loads everything into the DB

	def test_optimize(self):
		support.run_optimize(NFE=500, popsize=25)
