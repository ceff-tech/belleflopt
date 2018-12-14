import csv
import os
import logging

from eflows_optimization import settings
from eflows import models

log = logging.getLogger("eflows.optimization.support")

NO_DOWNSTREAM = ("OCEAN", "MEXICO", "CLOSED_BASIN")


def reset():
	load_hucs()
	load_species()
	load_climate()
	load_flows()


def _get_upstream(huc_object, force=False):
	if huc_object.upstream.count() > 0 and not force:
		return  # if this function is called when it already has upstream hucs defined, it's already complete - return immediately

	upstream = models.HUC.objects.filter(downstream_id=huc_object.id)  # get all the upstream of the current HUC
	for huc in upstream:  # for each upstream huc, find *its* upstream hucs and add them here too
		_get_upstream(huc)  # this needs to run for all the upstream hucs first
		huc.refresh_from_db()  # make sure it correctly gets the new info we just loaded for it

		if huc.upstream.count() > 0:
			for upstream_huc in huc.upstream.all():
				if upstream_huc.huc_id == huc.huc_id or upstream_huc.huc_id == huc_object.huc_id or (huc_object.downstream is not None and upstream_huc.huc_id == huc_object.downstream.huc_id):
					continue

				huc_object.upstream.add(upstream_huc)
	# now we can fill in the current huc with the upstream hucs filled
	# ON DEBUG - confirm that these instances will pick up upstream changes in recursive function

		huc_object.upstream.add(huc)  # add the upstream huc

	huc_object.save()


def load_hucs(filepath=os.path.join(settings.BASE_DIR, "data", "eel_hucs.csv")):
	with open(filepath, 'r') as huc_data:
		csv_data = csv.DictReader(huc_data)

		log.info("Loading HUCs")
		for row in csv_data:
			try:
				models.HUC.objects.get(huc_id=row["HUC_12"])
				continue  # if it exists, don't load it again
			except models.HUC.DoesNotExist:
				pass

			huc = models.HUC()
			huc.huc_id = row["HUC_12"]
			huc.save()  # we need to save before we can set the downstreams

	log.info("Loading Downstream information")
	with open(filepath, 'r') as huc_data:  # do it again to reset the cursor
		csv_data = csv.DictReader(huc_data)
		for row in csv_data:
			#log.debug("[{}]".format(row["HUC_12"]))
			huc = models.HUC.objects.get(huc_id=row["HUC_12"])
			if row["HU_12_DS"] not in NO_DOWNSTREAM:
				try:
					huc.downstream = models.HUC.objects.get(huc_id=row["HU_12_DS"])
				except models.HUC.DoesNotExist:
					log.error("Couldn't find downstream object {}".format(row["HU_12_DS"]))
					raise
			huc.save()

	_build_network()


def _build_network(force=False, starting_huc="180101051102"):
	"""
		Force runs *much* slower, but forces a full rebuild of the network
	:param force:
	:return:
	"""
	log.info("Building HUC network")
	#for huc in models.HUC.objects.all():
	huc = models.HUC.objects.get(huc_id=starting_huc)
	_get_upstream(huc, force=force)  # run it for everything to make sure it's complete


def load_species(filepath=os.path.join(settings.BASE_DIR, "data", "species_data.csv")):

	log.debug("Loading Species")

	with open(filepath, 'r') as species_data:
		species = csv.DictReader(species_data)
		for record in species:
			try:
				# get the fish
				fish = models.Species.objects.get(pisces_fid=record["FID"])
			except models.Species.DoesNotExist:
				# if it doesn't exist, create it
				fish = models.Species()
				fish.common_name = record["Common_Name"]
				fish.pisces_fid = record["FID"]
				fish.save()

			huc = models.HUC.objects.get(huc_id=record["HUC_12"])
			huc.assemblage.add(fish)
			huc.save()


def load_climate(filepath=os.path.join(settings.BASE_DIR, "data", "bcm_march86_eel.csv")):
	"""
		sets available water based on BCM data
	:return:
	"""
	log.debug("Loading Climate")

	with open(filepath, 'r') as climate_data:
		records = csv.DictReader(climate_data)

		for record in records:
			huc = models.HUC.objects.get(huc_id=record["HUC_12"])
			huc.initial_available_water = record["cfs_mainstem"]  # load the flow at the HUC outlet
			huc.save()


def load_flows(filepath=os.path.join(settings.BASE_DIR, "data", "flow_needs.csv")):

	log.debug("Loading Flows")

	# add the components themselves
	min_flow = models.FlowComponent(name="min_flow")
	max_flow = models.FlowComponent(name="max_flow")
	min_flow.save()
	max_flow.save()

	with open(filepath, 'r') as component_data:
		records = csv.DictReader(component_data)
		for record in records:
			log.debug(record.keys())
			species = models.Species.objects.get(common_name=record["species"])
			log.debug(species.id)
			min_component = models.SpeciesComponent(component=min_flow, species=species, value=record["min_flow"])
			max_component = models.SpeciesComponent(component=max_flow, species=species, value=record["max_flow"])
			min_flow.save()
			max_flow.save()
			species.save()
			min_component.save()
			max_component.save()

