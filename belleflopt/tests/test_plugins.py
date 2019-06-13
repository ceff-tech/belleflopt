"""
	Tests the plugin handling and loading code, not the plugins themselves
"""

import logging

from django.test import TestCase

from belleflopt import plugins
from belleflopt.plugins.environment import base

log = logging.getLogger("eflows.optimization.tests")
