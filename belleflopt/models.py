from django.db import models

from belleflopt import benefit

class Species(models.Model):
	common_name = models.CharField(null=False, max_length=255)
	pisces_fid = models.CharField(null=False, max_length=6)
	# presence = HUC objects

	def __repr__(self):
		return self.common_name

	def __str__(self):
		return self.common_name


class StreamSegment(models.Model):
	com_id = models.CharField(null=False, max_length=25)
	name = models.CharField(null=True, max_length=255, blank=True)  # include the name just for our own usefulness
	# components

	downstream = models.ForeignKey("self", null=True, on_delete=models.DO_NOTHING, related_name="upstream_single_huc")  # needs to be nullable for creation
	upstream = models.ManyToManyField("self", symmetrical=False, related_name="all_downstream_segments")  # we can build our upstream network once here!

	def __repr__(self):
		return "Segment {}: {}".format(self.com_id, self.name)

	def __str__(self):
		return "Segment {}: {}".format(self.com_id, self.name)


class FlowComponent(models.Model):
	"""
		This model more or less defines the components that are available - the segments
		relation and the intervening model is what relates components to stream segments
		and contains the actual data for a segment
	"""
	name = models.CharField(null=False, max_length=255)
	ceff_id = models.CharField(null=False, max_length=100)  # the ID used in CEFF for this component
	segments = models.ManyToManyField(StreamSegment, related_name="components", through="SegmentComponent")

	def __repr__(self):
		return self.name

	def __str__(self):
		return self.name


class SegmentComponent(models.Model):
	"""
		Related to StreamSegment and FlowComponent via the ManyToManyField on FlowComponent. Holds
		the data for a given flow component and segment
	"""
	# primary data for this component/segment
	pct_10 = models.FloatField()
	pct_25 = models.FloatField()
	pct_50 = models.FloatField()
	pct_75 = models.FloatField()
	pct_90 = models.FloatField()

	# the stream and component this data is for
	stream_segment = models.ForeignKey(StreamSegment, on_delete=models.DO_NOTHING)
	component = models.ForeignKey(FlowComponent, on_delete=models.DO_NOTHING)

	def __init__(self):
		"""
			We want to define our own because we'll attach non-Django benefit classes that we don't want to persist
			or be Django classes for performance reasons
		"""

		# self.benefit = benefit.BenefitBox()  # this will need to change, but is here to show the strategy - we'll probably have some kind of BenefitManager

		super().__init__()


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
