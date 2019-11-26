import django
from django.db import models

from belleflopt import flow_components

from eflows_optimization import settings


class StreamSegment(models.Model):
	CONNECTOR = "Connector"
	CANAL_DITCH = "CanalDitch"
	UNDERGROUND_CONDUIT = "UndergroundConduit"
	PIPELINE = "PIPELINE"
	STREAM_RIVER = "StreamRiver"
	ARTIFICIAL_PATH = "ArtificialPath"
	COASTLINE = "Coastline"

	FTYPE_CHOICES = [
		(CONNECTOR, CONNECTOR),
		(CANAL_DITCH, CANAL_DITCH),
		(UNDERGROUND_CONDUIT, UNDERGROUND_CONDUIT),
		(PIPELINE, PIPELINE),
		(STREAM_RIVER, STREAM_RIVER),
		(ARTIFICIAL_PATH, ARTIFICIAL_PATH),
		(COASTLINE, COASTLINE)
	]

	com_id = models.CharField(null=False, max_length=25, unique=True)
	name = models.CharField(null=True, max_length=255, blank=True)  # include the name just for our own usefulness
	ftype = models.CharField(null=True, blank=True, max_length=32, choices=FTYPE_CHOICES)
	strahler_order = models.PositiveSmallIntegerField(null=True, blank=True)
	total_upstream_area = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
	routed_upstream_area = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
	# components
	# species

	upstream_node_id = models.CharField(max_length=30)
	downstream_node_id = models.CharField(max_length=30)

	downstream = models.ForeignKey("self", null=True, on_delete=models.DO_NOTHING, related_name="upstream_single_huc")  # needs to be nullable for creation
	upstream = models.ManyToManyField("self", symmetrical=False, related_name="all_downstream_segments")  # we can build our upstream network once here!

	subwatershed = models.ForeignKey("HUC", null=True, on_delete=models.DO_NOTHING)  # keep it so we can potentially do aggregation in the future

	def __repr__(self):
		return "Segment {}: {}".format(self.com_id, self.name)

	def __str__(self):
		return "Segment {}: {}".format(self.com_id, self.name)

	#def __init__(self):
	#	"""
	#		We want to define our own because we'll attach non-Django benefit classes that we don't want to persist
	#		or be Django classes for performance reasons
	#	"""

	#	# We'll need some kind of item here that manages the benefit calculations of the subcomponents through time.
	#	# Might need one for environmental benefit and one for economic benefit
	#	# self.environmental_flows = None  # this will become a numpy series later of the daily allocated flows
	#	# self.economic_flows = None  # this will become a numpy series later of the daily allocated flows

	#	super().__init__()


class Species(models.Model):
	common_name = models.CharField(null=False, max_length=255)
	pisces_fid = models.CharField(null=False, max_length=6)
	segments = models.ManyToManyField(StreamSegment, related_name="species", through="SegmentPresence")

	def __repr__(self):
		return self.common_name

	def __str__(self):
		return self.common_name


class FlowComponent(models.Model):
	"""
		This model more or less defines the components that are available - the segments
		relation and the intervening model is what relates components to stream segments
		and contains the actual data for a segment
	"""
	name = models.CharField(null=False, max_length=255, unique=True)
	ceff_id = models.CharField(null=False, max_length=10)  # the ID used in CEFF for this component
	segments = models.ManyToManyField(StreamSegment, related_name="components", through="SegmentComponent")

	def __repr__(self):
		return self.name

	def __str__(self):
		return self.name


class FlowMetric(models.Model):
	"""
		Just defining available metrics - no data in here really
	"""

	components = models.ManyToManyField(FlowComponent, related_name="metrics")  # this is many to many because winter components share timing and duration
	characteristic = models.CharField(max_length=100)  # mostly a description
	metric = models.CharField(max_length=50, unique=True)  # the CEFF short code for it
	description = models.TextField()

	def __repr__(self):
		return "{} - {}".format(self.characteristic, self.metric)

	def __str__(self):
		return self.__repr__()


class SegmentComponent(models.Model):
	"""
		Related to StreamSegment and FlowComponent via the ManyToManyField on FlowComponent. Holds
		the data for a given flow component and segment.

		Ramp values correspond to q1 and q4 in our benefit boxes - they're where we start ramping benefit up from
		0 or where the ramp down hits 0. The start and end values and min/max values correspond to q2 and q3 in the boxes
		and are where benefit hits its max
	"""

	class Meta:
		unique_together = ['stream_segment', 'component']

	start_day_ramp = models.PositiveSmallIntegerField(null=True)
	start_day = models.PositiveSmallIntegerField(null=True)  # we need to allow these to be null because of the way we build them
	duration = models.PositiveSmallIntegerField(null=True)  # we're working in days right now - if we were working in seconds, we might consider a DurationField instead
	duration_ramp = models.PositiveSmallIntegerField(null=True)
	# end_day is a property calculated from start_day and duration
	# end_day_ramp is a property calculated from start_day and duration_ramp

	minimum_magnitude_ramp = models.DecimalField(max_digits=10, decimal_places=2, null=True)
	minimum_magnitude = models.DecimalField(max_digits=10, decimal_places=2, null=True)
	maximum_magnitude = models.DecimalField(max_digits=10, decimal_places=2, null=True)
	maximum_magnitude_ramp = models.DecimalField(max_digits=10, decimal_places=2, null=True)

	# the stream and component this data is for
	stream_segment = models.ForeignKey(StreamSegment, on_delete=models.DO_NOTHING)
	component = models.ForeignKey(FlowComponent, on_delete=models.DO_NOTHING)

	def build(self, builder=None):
		"""
			The builder should fill in the main values of this flow component based on the values of its flow metrics
		:param builder:
		:return:
		"""

		if builder is None:  # if a builder isn't passed in, get the default one from flow_components.py as defined for this component type in local_settings
			builder = getattr(flow_components, settings.COMPONENT_BUILDER_MAP[self.component.ceff_id])
		elif not hasattr(builder, "__call__"):  # if they didn't pass in a callable, tell them that
			raise ValueError("Must provide a callable function to `build` as the builder for this segment component.")

		if self.component.ceff_id == "Peak":
			pass

		builder(self)  # modifies this object's values, so we need to save it next
		self.save()

	def make_benefit(self, benefit_maker=None):
		"""
			This method is transient and must be called prior to each optimization because it builds a BenefitBox
			object that doesn't persist in the database
		:param benefit_maker: A function that takes this object as a parameter and returns a BenefitBox object
				with the all values populated so that benefit can be quantified. If not provided, defaults are used
		:return:
		"""
		if benefit_maker is None:  # if a maker isn't passed in, get the default one from flow_components.py as defined for this component type in local_settings
			benefit_maker = getattr(flow_components, settings.BENEFIT_MAKER_MAP[self.component.ceff_id])
		elif not hasattr(benefit_maker, "__call__"):  # if they didn't pass in a callable, tell them that
			raise ValueError("Must provide a callable function to make_benefit as the benefit_maker.")

		self.benefit = benefit_maker(self)  # benefit_maker just returns a benefit object, so make that the benefit attribute on this instance

	@property
	def end_day(self):
		return self.start_day + self.duration

	@property
	def end_day_ramp(self):
		return self.start_day + self.duration_ramp


class SegmentComponentDescriptor(models.Model):
	"""
		Raw data for each flow component spec - straight out of the spreadsheet. SegmentComponents will be built from
		this. I think these are equivalent to the functional flow metrics (FFMs).
	"""

	#class Meta:
	#	unique_together = ['flow_component', 'flow_metric']  # flow component is unique because it's using SegmentComponent

	flow_components = models.ManyToManyField(SegmentComponent, related_name="descriptors")  # this is many to many because winter components share timing and duration
	flow_metric = models.ForeignKey(FlowMetric, on_delete=models.CASCADE, related_name="descriptors")
	source_type = models.CharField(max_length=30, null=True)  # source in spreadsheet
	source_name = models.CharField(max_length=30, null=True)  # source2
	notes = models.TextField(null=True, blank=True)

	# OK, so this next field is awful, but I have a good reason. With the switch of .flow_components from a foreign key
	# to a many to many field, there's not a good way to bulk create these objects while keeping track of the segment
	# components they attach to because M2M fields require this to already have a pk to create the association, and that
	# doesn't happen until save is called. When using bulk create, we also don't get pks attached to the existing objects,
	# except with postgres, so we can't just store them and their associations until after creation, then create the
	# actual associations. So what we'll do is temporarily store the PKs of the segment components we want to attach this
	# object to in associated_components_holding_dont_use as comma separated values. Then after bulk creation, we'll
	# iterate through and create the associations, then null out this field.
	# Yes, this is super ugly and silly, but we're talking the difference between *days* to load data and an hour or so.
	# It's worth it to have one tiny null attribute hanging around, I think.

	associated_components_holding_dont_use = models.CharField(max_length=1024, null=True, blank=True)

	# primary data for this component/segment
	pct_10 = models.DecimalField(max_digits=10, decimal_places=2)
	pct_25 = models.DecimalField(max_digits=10, decimal_places=2)
	pct_50 = models.DecimalField(max_digits=10, decimal_places=2)
	pct_75 = models.DecimalField(max_digits=10, decimal_places=2)
	pct_90 = models.DecimalField(max_digits=10, decimal_places=2)


class SegmentPresence(models.Model):
	"""
		The through model for species presence, since we're storing the probability of occurrence on the segment
	"""
	stream_segment = models.ForeignKey(StreamSegment, on_delete=models.DO_NOTHING)
	species = models.ForeignKey(Species, on_delete=models.DO_NOTHING)

	probability = models.DecimalField(max_digits=4, decimal_places=3)


class HUC(models.Model):
	huc_id = models.CharField(null=False, max_length=13)
	downstream = models.ForeignKey("self", null=True, on_delete=models.DO_NOTHING, related_name="upstream_single_huc")  # needs to be nullable for creation
	upstream = models.ManyToManyField("self", symmetrical=False, related_name="upstream_relationship_dont_use")  # we can build our upstream network once here!

	assemblage = models.ManyToManyField(Species, related_name="presence")
	initial_available_water = models.DecimalField(null=True, max_digits=8, decimal_places=2)  # how much water do we start with - from climate data
	flow_allocation = models.DecimalField(null=True, max_digits=8, decimal_places=2)  # how much water does it try to use in this HUC?

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

	@property
	def huc_8(self):
		return self.huc_id[:8]


class ModelRun(models.Model):
	name = models.CharField(max_length=255, null=True, blank=True)
	date_run = models.DateTimeField(default=django.utils.timezone.now)


class FlowBenefitResult(models.Model):
	"""
		Stores flow and benefit allocations for a specific day of the water year, model run and iteration of that run
	"""
	model_run = models.ForeignKey(ModelRun, on_delete=models.CASCADE)
	model_iteration = models.IntegerField()   # which iteration of the model does this correspond to?
	available_flow = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	environmental_flow = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	environmental_benefit = models.FloatField()
	economic_flow = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	economic_benefit = models.FloatField()
	day_of_water_year = models.SmallIntegerField()
