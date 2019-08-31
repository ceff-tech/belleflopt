from django.db import models

class Species(models.Model):
	common_name = models.CharField(null=False, max_length=255)
	pisces_fid = models.CharField(null=False, max_length=6)
	# presence = HUC objects
	# components = flow component relationship

	def __repr__(self):
		return self.common_name

	def __str__(self):
		return self.common_name

class HUC(models.Model):
	huc_id = models.CharField(null=False, max_length=13)
	downstream = models.ForeignKey("self", null=True, on_delete=models.DO_NOTHING, related_name="upstream_single_huc")  # needs to be nullable for creation
	upstream = models.ManyToManyField("self", symmetrical=False, related_name="upstream_relationship_dont_use")  # we can build our upstream network once here!

	assemblage = models.ManyToManyField(Species, related_name="presence")
	initial_available_water = models.FloatField(null=True)  # how much water do we start with - from climate data
	flow_allocation = models.FloatField(null=True)  # how much water does it try to use in this HUC?

	@property
	def upstream_total_flow(self):
		"""
			The inflow to this HUC if all upstream hucs didn't use any water
		:return:
		"""
		return sum([up_huc.initial_available_water for up_huc in self.upstream.all() if
			 			up_huc.initial_available_water is not None])

	@property
	def max_possible_flow(self):
		"""
			The outflow from this HUC if all upstream hucs didn't use any water
		:return:
		"""
		return self.upstream_total_flow + self.initial_available_water


class FlowComponent(models.Model):
	name = models.CharField(null=False, max_length=255)
	# month
	species = models.ManyToManyField(Species, related_name="components", through="SpeciesComponent")

	def __repr__(self):
		return self.name

	def __str__(self):
		return self.name


class SpeciesComponent(models.Model):
	"""
		Related to Species and FlowComponent via the ManyToManyField on FlowComponent
	"""
	value = models.FloatField()
	species = models.ForeignKey(Species, on_delete=models.DO_NOTHING)
	component = models.ForeignKey(FlowComponent, on_delete=models.DO_NOTHING)
	threshold = models.FloatField(default=0.8)  # threshold * value is the point above which we consider a need met, but we'd like to get to value

