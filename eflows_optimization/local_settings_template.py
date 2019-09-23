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

WINTER_PEAK_MAGNITUDE_METRIC = "Peak_20"  # which modeled metric should we use for winter peak magnitude
WINTER_PEAK_START_TIMING_METRIC = "Wet_Tim"  # which metric contains start timing for this flow component? This one is a bit different, AND NOT YET READY, because the peak flow component will need to handle it a bit differently and make sure it hits the magnitude values as many times as specified in the frequency during the period specified by start timing and duration of the winter baseflow
WINTER_PEAK_START_TIMING_VALUES = ("pct_10", "pct_25")  # which fields on the start timing metric should be q1 and q2 for timing
WINTER_PEAK_DURATION_METRIC = "Peak_Dur_20"  # which metric will have the duration value for winter peak?
WINTER_PEAK_DURATION_VALUES = ("pct_75", "pct_90")  # Used to set q3 and q4 based on start timing values plus duration pulled from duration metric in fields specified here

WINTER_BASEFLOW_MAGNITUDE_METRIC = "Wet_BFL_Mag_50"  # which modeled metric should we use for winter baseflow magnitude
WINTER_BASEFLOW_START_TIMING_METRIC = "Wet_Tim"  # which metric contains start timing for this flow component?
WINTER_BASEFLOW_START_TIMING_VALUES = ("pct_10", "pct_25")  # which fields on the start timing metric should be q1 and q2 for timing
WINTER_BASEFLOW_DURATION_METRIC = "Wet_BFL_Dur"  # which metric will have the duration value for winter baseflow?
WINTER_BASEFLOW_DURATION_VALUES = ("pct_75", "pct_90")  # Used to set q3 and q4 based on start timing values plus duration pulled from duration metric in fields specified here