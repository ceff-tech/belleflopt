from django.test import TestCase

import seaborn
import pandas
from matplotlib import pyplot as plt

from belleflopt import benefit, models, load


class TestPeakBenefit(TestCase):
	def setUp(self):
		self.goodyears_bar = 8058513
		# set up the DB
		load.load_flow_components()
		load.load_flow_metrics()

		gy_segment = models.StreamSegment(com_id=self.goodyears_bar, routed_upstream_area=0, total_upstream_area=0)
		gy_segment.save()
		gy_segment_component = models.SegmentComponent(stream_segment=gy_segment, component=models.FlowComponent.objects.get(ceff_id="DS"))
		gy_segment_component.save()

				# p10, p25, p50, p75, p90
		ffms = {"DS_Dur_WS": [84.67, 114.63, 145.00, 176.50, 201.52],
		        "DS_Mag_50": [35.50, 53.72, 83.01, 122.76, 144.62],
		        "DS_Mag_90": [72.09, 101.84, 156.52, 233.21, 333.91],
		        "DS_Tim": [278.82, 288.00, 300.90, 311.50, 324.13,],
		        }

		# attach the descriptors
		for metric in ffms:
			descriptor = models.SegmentComponentDescriptor(
				flow_metric=models.FlowMetric.objects.get(metric=metric),
				pct_10=ffms[metric][0],
				pct_25=ffms[metric][1],
				pct_50=ffms[metric][2],
				pct_75=ffms[metric][3],
				pct_90=ffms[metric][4],
			)
			descriptor.save()
			descriptor.flow_components.add(gy_segment_component)

		load.build_segment_components(simple_test=False)  # build the segment components so we can use benefit later

		self.x = list(range(1, 366))
		self.goodyears_bar_flows = [111, 111, 112, 146, 146, 133, 127, 122, 118, 118, 118, 116, 114, 112, 112, 112, 111,
		                            111, 111, 110, 110, 111, 111, 111, 111, 111, 111, 110, 110, 110, 110, 109, 109, 108,
		                            108, 108, 108, 108, 109, 109, 109, 110, 110, 110, 111, 112, 112, 112, 112, 112, 111,
		                            134, 322, 492, 600, 315, 200, 165, 261, 587, 500, 388, 385, 220, 172, 169, 160, 153,
		                            151, 150, 148, 146, 145, 143, 143, 148, 157, 297, 218, 189, 177, 239, 252, 212, 420,
		                            604, 346, 275, 235, 217, 209, 196, 179, 180, 176, 172, 182, 251, 401, 349, 630, 807,
		                            511, 397, 339, 306, 334, 1420, 2990, 1530, 1170, 1850, 1890, 1200, 919, 775, 679,
		                            618, 585, 574, 575, 571, 561, 566, 1140, 1290, 1400, 1040, 833, 718, 658, 673, 658,
		                            587, 545, 892, 5610, 3270, 2040, 1550, 1240, 1060, 970, 879, 794, 734, 701, 755,
		                            1760, 2410, 2570, 1780, 1770, 2440, 2570, 2090, 3470, 3620, 2690, 2120, 1750, 1510,
		                            1350, 1210, 1100, 1030, 998, 1010, 1090, 1170, 1340, 1330, 1250, 1300, 1210, 1170,
		                            1360, 1890, 2040, 1680, 1500, 1420, 1440, 2140, 2430, 2210, 2180, 2170, 2280, 3050,
		                            5380, 3510, 2800, 2380, 2170, 2190, 2260, 2120, 1990, 2160, 2600, 2760, 2640, 2570,
		                            2670, 3120, 3520, 3600, 3510, 3320, 3060, 2900, 2470, 2320, 2300, 2240, 2300, 2420,
		                            2690, 2860, 2900, 2800, 2690, 2820, 2960, 2840, 2770, 3330, 2640, 2270, 2210, 1900,
		                            1920, 1850, 1850, 1870, 2050, 2130, 1930, 1970, 2200, 2450, 2630, 2820, 2980, 3230,
		                            3360, 3460, 3470, 3050, 2520, 2300, 2300, 2460, 2450, 2370, 2320, 2250, 2110, 1990,
		                            1920, 1850, 1760, 1580, 1370, 1240, 1190, 1130, 1070, 995, 921, 864, 815, 784, 752,
		                            726, 699, 678, 660, 641, 611, 586, 566, 549, 531, 513, 493, 473, 462, 451, 436, 424,
		                            413, 403, 391, 377, 366, 357, 348, 339, 331, 323, 313, 307, 302, 296, 291, 285, 282,
		                            277, 272, 268, 264, 264, 271, 260, 254, 246, 240, 238, 239, 235, 232, 229, 225, 224,
		                            222, 219, 216, 213, 209, 206, 203, 203, 200, 198, 194, 192, 192, 190, 192, 187, 186,
		                            188, 193, 195, 188, 182, 179, 177, 221, 234, 218, 275, 222, 203, 196, 191, 187, 184,
		                            181, 180, 202, 227, 241]

	def _plot_benefit(self, peak_benefit, base_benefit, segment_component=None, save_path=None):
		base_data = {
			"Days": self.x,
			"Base Benefit": base_benefit,
			"Peak-Adjusted Benefit": peak_benefit
		}
		pd_data = pandas.DataFrame(base_data, columns=base_data.keys())

		seaborn.lineplot("Days", "Peak-Adjusted Benefit", data=pd_data, label="Peak-Adjusted Benefit")
		seaborn.lineplot("Days", "Base Benefit", data=pd_data, label="Base Benefit")

		if segment_component:
			plt.title(
				"Base and peak benefit for {} on segment {}".format(segment_component.component.name, segment_component.stream_segment.com_id))
		plt.ylabel("Benefit")
		plt.xlabel("Day of water year")
		if save_path is not None:
			plt.savefig(save_path)
		plt.show()

	def test_segment_data(self):
		segment_component = models.SegmentComponent.objects.get(component__ceff_id="DS",
		                                                        stream_segment__com_id=self.goodyears_bar)
		segment_component.make_benefit()


		segment_component.benefit.plot_annual_benefit(screen=False, y_lim=(10, 175))
		#seaborn.lineplot(self.x, self.goodyears_bar_flows, color="black")
		plt.savefig(r"C:\Users\dsx\Dropbox\Graduate\Thesis\figures\base_benefit_examples\goodyears_dry_season.png",
		            dpi=600)
		plt.show()

		segment_component.benefit.plot_flow_benefit(screen=False, day_of_year=90)
		plt.savefig(r"C:\Users\dsx\Dropbox\Graduate\Thesis\figures\base_benefit_examples\goodyears_dry_season_day90.png",
		            dpi=600)
		plt.show()