from belleflopt import benefit

metric_flow_mapping = {
	""
}



class BaseFlowComponentBenefitManager(object):
	pass


class SpringRecessionBenefitManager(BaseFlowComponentBenefitManager):
	pass


class SummerBaseFlowBenefitManager(BaseFlowComponentBenefitManager):
	pass


class FallInitiationBenefitManager(BaseFlowComponentBenefitManager):
	pass


class WinterBaseFlowBenefitManager(BaseFlowComponentBenefitManager):
	pass


class WinterPeakFlowBenefitManager(BaseFlowComponentBenefitManager):
	pass

id_manager_map = {
	"Mag_50": SummerBaseFlowBenefitManager,
	"Peak_20": WinterPeakFlowBenefitManager,
}