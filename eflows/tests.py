import logging

from django.test import TestCase

from . import models
from . import support

log = logging.getLogger("eflows.optimization.tests")


class TestHUCNetwork(TestCase):

	def setUp(self):
		support.load_hucs()

	def _print_and_check_huc_info(self, ID, name, expected_upstream):

		tow = models.HUC.objects.get(huc_id=ID)
		log.debug("{} {} has {} upstream hucs".format(name, ID, tow.upstream.count()))
		log.debug("upstream HUCs, if any, are {}".format([huc.huc_id for huc in tow.upstream.all()]))
		self.assertEqual(tow.upstream.count(), expected_upstream)

	def test_huc_load(self):

		ridgeline_huc = "180101050801"  # 0 upstream
		small_upstream_huc = "180101050803"  # 2 upstream
		mid_upstream_huc = "180101050906"  # 11 upstream

		self._print_and_check_huc_info(ridgeline_huc, "Ridgeline HUC", 0)
		self._print_and_check_huc_info(small_upstream_huc, "Small Upstream", 2)
		self._print_and_check_huc_info(mid_upstream_huc, "Mid Upstream", 11)

	def test_species_load(self):
		support.load_species()

		flow_sensitive = ["CGO01", "CCK01", "CGC01", "SOT04", "CLS01", "SOM05",
							"SOK01", "SOT08", "SOT07", "SOT06", "SOT05", "OHP01",
							"CCM02", "CMC01", "GGA02", "CLS09", "SOM13", "PLH01",
							"SOM04", "SOM03", "PES01", "CCS01", "SOC03", "CCP01",
							"CRO02", "OST01", "CCL01", "CCK02", "CCM01", "CLE03",
							"CCO03", "SPW01", "SOM02", "SOM01", "AAM01", "CLS08",
							"GEN01", "CCR02", "CRO04", "CSB06", "PET01", "CCP02",
							"CXT01", "CLS02", "CCG01", "PLA01", "CLE01", "CAI01",
							"CPG01", "CRO01", "CPM01", "CCO01", "EHT01", "CRO07",
							"CCS02", "CCB01", "SOM07", "SOM08", "SOK02", "CLS05",
							"AAM02", "GEK01", "GGA03", "CCK03", "SOT01", "SOT02",
							"PLR01", "AAT01"]

		not_found = 0
		for fid in flow_sensitive:
			try:
				models.Species.objects.get(pisces_fid=fid)  # just make sure we can get it
			except models.Species.DoesNotExist:
				log.debug("{} not in database".format(fid))
				not_found += 1

		# There are 55 flow sensitive species not in the Eel (of 68)
		print("Not found species: {}".format(not_found))

		# This isn't a great test, but it'll do for now - probably worth expanding in the future
		# if we continue using this (as opposed to loading data straight from PISCES)
		self.assertEqual(not_found, 55)

	def test_flow_available(self):
		support.load_climate()

		for huc in models.HUC.objects.all():
			self.assertIsNotNone(huc.initial_available_water)
			self.assertGreaterEqual(huc.initial_available_water, 0)

