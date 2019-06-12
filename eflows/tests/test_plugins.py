"""
	Tests the plugin handling and loading code, not the plugins themselves
"""

import logging

from django.test import TestCase

from eflows import plugins
from eflows.plugins.environment import base

log = logging.getLogger("eflows.optimization.tests")

class PluginLoadingTest(TestCase):
	def test_load_environment_base(self):
		"""
			Plugins need a rethink - I shouldn't load them the way I'm loading them. Should just use standard import
			mechanisms since I'm going to use Python to load rather than runs configured in the DB. Trying to find
			the plugins using strings is a pain in the butt
		:return:
		"""
		self.assertIs(plugins.return_plugin_function("eflows.plugins.environment.base", "environment_benefit"), base.environment_benefit)
