# Generated by Django 2.2.4 on 2019-11-15 01:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('belleflopt', '0017_auto_20191017_1749'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='flowmetric',
            name='component',
        ),
        migrations.AddField(
            model_name='flowmetric',
            name='components',
            field=models.ManyToManyField(related_name='metrics', to='belleflopt.FlowComponent'),
        ),
        migrations.AddField(
            model_name='segmentcomponentdescriptor',
            name='flow_components',
            field=models.ManyToManyField(related_name='descriptors', to='belleflopt.SegmentComponent'),
        ),
        migrations.AlterField(
            model_name='segmentcomponent',
            name='maximum_magnitude',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='segmentcomponent',
            name='maximum_magnitude_ramp',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='segmentcomponent',
            name='minimum_magnitude',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='segmentcomponent',
            name='minimum_magnitude_ramp',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='segmentcomponentdescriptor',
            name='flow_metric',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='descriptors', to='belleflopt.FlowMetric'),
        ),
        migrations.AlterUniqueTogether(
            name='segmentcomponentdescriptor',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='segmentcomponentdescriptor',
            name='flow_component',
        ),
    ]
