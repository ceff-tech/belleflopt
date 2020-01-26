import unittest
from belleflopt.support import day_of_water_year, water_year


class TestWaterYearDates(unittest.TestCase):
	def test_day_of_water_year(self):
		self.assertEqual(1, day_of_water_year(2010, 10, 1))
		self.assertEqual(1, day_of_water_year(2020, 10, 1))
		self.assertEqual(366, day_of_water_year(2020, 9, 30))  # leap year water year will have day 366
		self.assertEqual(365, day_of_water_year(2019, 9, 30))  # normal water year ending on day 365
		self.assertEqual(92, day_of_water_year(2020, 12, 31))  # but dec 31 should always be the same
		self.assertEqual(92, day_of_water_year(2019, 12, 31))

		# Just confirm for our own sanity (and if someone changes it so we don't use arrow anymore) that leap years are correct
		self.assertRaises(ValueError, day_of_water_year, 2019, 2, 29)
		self.assertEqual(151, day_of_water_year(2019, 2, 28))
		self.assertEqual(151, day_of_water_year(2020, 2, 28))
		self.assertEqual(152, day_of_water_year(2020, 2, 29))
		self.assertEqual(153, day_of_water_year(2020, 3, 1))
		self.assertEqual(152, day_of_water_year(2019, 3, 1))

	def test_water_year(self):
		self.assertEqual(2019, water_year(2019, 2))
		self.assertEqual(2018, water_year(2018, 2))
		self.assertEqual(2019, water_year(2018, 12))
		self.assertEqual(2019, water_year(2018, 10))
		self.assertEqual(2018, water_year(2018, 9))
		self.assertEqual(2019, water_year(2019, 9))
		self.assertEqual(2020, water_year(2019, 10))


if __name__ == '__main__':
	unittest.main()
