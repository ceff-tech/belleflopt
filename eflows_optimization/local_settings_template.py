import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'FSAH*GIFASUIFJASIOFNASTIOUAWfgsdhuiogtweabtp9iA{ORJSOFIhjs'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

COMPONENT_BUILDER_MAP = {  # not a true plugin system yet, but people can put code in the flow_components file and modify
    # these settings and it will change the behavior of the code. It'd be nice to be able to simply indicate a plugin
    # to handle benefit functions, but that's getting a bit too far ahead at the moment.
	"FA": "fall_initiation_builder",
	"Wet_BFL": "winter_base_flow_builder",
	"Peak": "winter_peak_flow_builder",
	"SP": "spring_recession_builder",
	"DS": "summer_base_flow_builder"
}

BENEFIT_MAKER_MAP = {  # these are function names that will be looked up in flow_components.py when a function isn't explicitly provided
    "FA": "fall_initiation_benefit_maker",
    "Wet_BFL": "winter_baseflow_benefit_maker",
    "Peak": "winter_peak_flow_benefit_maker",
    "SP": "spring_recession_benefit_maker",
    "DS": "summer_base_flow_benefit_maker"
}

SUMMER_BASEFLOW_MAGNITUDE_METRIC = "DS_Mag_50"  # which modeled metric should we use for summer baseflow magnitude
SUMMER_BASEFLOW_START_TIMING_METRIC = "DS_Tim"  # which metric contains start timing for this flow component?
SUMMER_BASEFLOW_START_TIMING_VALUES = ("pct_10", "pct_25")  # which fields on the start timing metric should be q1 and q2 for timing
SUMMER_BASEFLOW_DURATION_METRIC = "DS_Dur_WS"  # which metric will have the duration value for summer?
SUMMER_BASEFLOW_DURATION_VALUES = ("pct_75", "pct_90")  # Used to set q3 and q4 based on start timing values plus duration pulled from duration metric in fields specified here

WINTER_PEAK_MAGNITUDE_METRIC = "Peak_50"  # which modeled metric should we use for winter peak magnitude
WINTER_PEAK_START_TIMING_METRIC = "Wet_Tim"  # which fields on the start timing metric should be q1 and q2 for timing
WINTER_PEAK_START_TIMING_VALUES = ("pct_10", "pct_25")  # which fields on the start timing metric should be q1 and q2 for timing
WINTER_PEAK_DURATION_VALUES = ("pct_75", "pct_90")  # Used to set q3 and q4 based on start timing values plus duration pulled from duration metric in fields specified here
WINTER_PEAK_DURATION_METRIC = "Wet_BFL_Dur"

WINTER_PEAK_EVENT_FREQUENCY_METRIC = "Peak_Fre_50"
WINTER_PEAK_EVENT_DURATION_METRIC = "Peak_Dur_20"
WINTER_PEAK_EVENT_FREQUENCY_VALUE = "pct_50"
WINTER_PEAK_EVENT_DURATION_VALUE = "pct_50"
WINTER_PEAK_EVENT_STARTING_BENEFIT = 10  # normally benefit is "1" - so a benefit of 10 makes a winter flow much more beneficial, but it tails off quickly

WINTER_BASEFLOW_MAGNITUDE_METRIC = "Wet_BFL_Mag_50"  # which modeled metric should we use for winter baseflow magnitude
WINTER_BASEFLOW_START_TIMING_METRIC = "Wet_Tim"  # which metric contains start timing for this flow component?
WINTER_BASEFLOW_START_TIMING_VALUES = ("pct_10", "pct_25")  # which fields on the start timing metric should be q1 and q2 for timing
WINTER_BASEFLOW_DURATION_METRIC = "Wet_BFL_Dur"  # which metric will have the duration value for winter baseflow?
WINTER_BASEFLOW_DURATION_VALUES = ("pct_75", "pct_90")  # Used to set q3 and q4 based on start timing values plus duration pulled from duration metric in fields specified here

FALL_INITIATION_MAGNITUDE_METRIC = ""  # which modeled metric should we use for winter baseflow magnitude
FALL_INITIATION_START_TIMING_METRIC = ""  # which metric contains start timing for this flow component?
FALL_INITIATION_START_TIMING_VALUES = ("pct_10", "pct_25")  # which fields on the start timing metric should be q1 and q2 for timing
FALL_INITIATION_DURATION_METRIC = ""  # which metric will have the duration value for winter baseflow?
FALL_INITIATION_DURATION_VALUES = ("pct_75", "pct_90")  # Used to set q3 and q4 based on start timing values plus duration pulled from duration metric in fields specified here

FALL_INITIATION_FREQUENCY = 1  # this only happens once in the season officially
FALL_INITIATION_EVENT_STARTING_BENEFIT = 5  # normally benefit is "1" - so a benefit of 10 makes a winter flow much more beneficial, but it tails off quickly
FALL_INITIATION_EVENT_DURATION_VALUE = "pct_50"

# The names and folder of the FFM data to load
LOAD_FFM_FOLDER = os.path.join(BASE_DIR, "data", "ffm_modeling", "Data", "NHD FFM predictions")

LOAD_FFMS = [SUMMER_BASEFLOW_MAGNITUDE_METRIC,
             SUMMER_BASEFLOW_DURATION_METRIC,
             SUMMER_BASEFLOW_START_TIMING_METRIC,
             WINTER_PEAK_DURATION_METRIC,
             WINTER_PEAK_START_TIMING_METRIC,
             WINTER_PEAK_MAGNITUDE_METRIC,
             WINTER_BASEFLOW_DURATION_METRIC,
             WINTER_BASEFLOW_MAGNITUDE_METRIC,
             WINTER_BASEFLOW_DURATION_METRIC,]

LOAD_FFM_SUFFIX = "_NHD_pred_range.csv"

# COLORS
# Primary color scheme at http://paletton.com/#uid=43k0I0koVuLfcI0kqzutVrkvtln

# used http://www.zonums.com/online/color_ramp/ with color scheme colors and variations
# of 35, 139, 149
# 100
# 245, 199, 54
# 20
# 245, 144, 54
DEFAULT_COLORRAMP = ["#238B95","#258B94","#278C93","#298C92","#2B8D91","#2D8D90","#2F8E8F","#318F8E","#338F8D","#35908C","#37908B","#39918A","#3B9289","#3E9288","#409387","#429386","#449485","#469585","#489584","#4A9683","#4C9682","#4E9781","#509880","#52987F","#54997E","#56997D","#599A7C","#5B9B7B","#5D9B7A","#5F9C79","#619C78","#639D77","#659E76","#679E75","#699F75","#6B9F74","#6DA073","#6FA072","#72A171","#74A270","#76A26F","#78A36E","#7AA36D","#7CA46C","#7EA56B","#80A56A","#82A669","#84A668","#86A767","#88A866","#8AA865","#8DA965","#8FA964","#91AA63","#93AB62","#95AB61","#97AC60","#99AC5F","#9BAD5E","#9DAE5D","#9FAE5C","#A1AF5B","#A3AF5A","#A5B059","#A8B158","#AAB157","#ACB256","#AEB255","#B0B355","#B2B354","#B4B453","#B6B552","#B8B551","#BAB650","#BCB64F","#BEB74E","#C1B84D","#C3B84C","#C5B94B","#C7B94A","#C9BA49","#CBBB48","#CDBB47","#CFBC46","#D1BC45","#D3BD45","#D5BE44","#D7BE43","#D9BF42","#DCBF41","#DEC040","#E0C13F","#E2C13E","#E4C23D","#E6C23C","#E8C33B","#EAC43A","#ECC439","#EEC538","#F0C537","#F2C636","#F5C736","#F5C436","#F5C136","#F5BF36","#F5BC36","#F5B936","#F5B736","#F5B436","#F5B236","#F5AF36","#F5AC36","#F5AA36","#F5A736","#F5A436","#F5A236","#F59F36","#F59D36","#F59A36","#F59736","#F59536","#F59236","#F59036",]
DEFAULT_COLORRAMP_BLUE_ORANGE = ["#238B95","#2D8B90","#378B8B","#418B87","#4B8B82","#558C7E","#5F8C79","#698C75","#738C70","#7D8D6C","#878D67","#918D63","#9B8D5E","#A58E5A","#AF8E55","#B98E51","#C38E4C","#CD8F48","#D78F43","#E18F3F","#EB8F3A","#F59036"]
DEFAULT_COLORRAMP_BLUE_YELLOW_ORANGE = ["#238B95","#2B8D91","#338F8D","#3B918A","#439486","#4B9682","#53987F","#5B9B7B","#639D77","#6B9F74","#73A270","#7BA46C","#83A669","#8CA965","#94AB61","#9CAD5E","#A4AF5A","#ACB256","#B4B453","#BCB64F","#C4B94B","#CCBB48","#D4BD44","#DCC040","#E4C23D","#ECC439","#F5C736","#F5AB36","#F59036"]