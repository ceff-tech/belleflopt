from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from belleflopt import models


@receiver(m2m_changed, sender=models.SegmentComponentDescriptor.flow_components.through)
def segment_component_descriptor_unique_check(sender, instance, action, **kwargs):
	if action != "pre_add":  # we only care about the pre-add action, not any others
		return

	for segment_component in instance.segment_components.all():
		if models.SegmentComponent.objects.get(stream_segment=segment_component,
												descriptors__flow_metric=instance.flow_metric):
			raise ValueError("Can't attach Descriptor with flow metric {} to SegmentComponent with component {} and"
								" com_id {}. It already has a Descriptor for this flow metric".format(
								instance.flow_metric.metric,
								segment_component.component.name,
								segment_component.stream_segment.com_id)
			)