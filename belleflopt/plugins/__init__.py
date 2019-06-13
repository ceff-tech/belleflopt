import importlib
from belleflopt

def return_plugin_function(package, entry_point):
	"""
		Given a plugin to be used, imports the plugin, then returns the object for the
		entry point
	:param package: a package in dot format within the plugins folder. For example, the base
		package for environmental objectives would be 'eflows.plugins.environment.base'
	:param entry_point:
	:return:
	"""

	importlib.import_module(package)
	return getattr(globals()[package], entry_point)
