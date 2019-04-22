from dagster import Enum, EnumValue

from dagster.core.types.runtime import Stringish
from dagster.utils import safe_isfile


class FileExistsAtPath(Stringish):
    def __init__(self):
        super(FileExistsAtPath, self).__init__(description='A path at which a file actually exists')

    def coerce_runtime_value(self, value):
        value = super(FileExistsAtPath, self).coerce_runtime_value(value)
        return self.throw_if_false(safe_isfile, value)


EmrActionOnFailureTerminateJobFlow = EnumValue('TERMINATE_JOB_FLOW')
EmrActionOnFailureTerminateCluster = EnumValue('TERMINATE_CLUSTER')
EmrActionOnFailureCancelAndWait = EnumValue('CANCEL_AND_WAIT')
EmrActionOnFailureContinue = EnumValue('CONTINUE')
EmrActionOnFailure = Enum(
    name='EmrActionOnFailure',
    enum_values=[
        EmrActionOnFailureTerminateJobFlow,
        EmrActionOnFailureTerminateCluster,
        EmrActionOnFailureCancelAndWait,
        EmrActionOnFailureContinue,
    ],
)

EmrSupportedProductsMapRM3 = EnumValue('mapr-m3')
EmrSupportedProductsMapRM5 = EnumValue('mapr-m5')
EmrSupportedProducts = Enum(
    name='EmrSupportedProducts',
    enum_values=[EmrSupportedProductsMapRM3, EmrSupportedProductsMapRM5],
)

EmrScaleDownBehaviorTerminateAtInstanceHour = EnumValue('TERMINATE_AT_INSTANCE_HOUR')
EmrScaleDownBehaviorTerminateAtTaskCompletion = EnumValue('TERMINATE_AT_TASK_COMPLETION')
EmrScaleDownBehavior = Enum(
    name='EmrScaleDownBehavior',
    enum_values=[
        EmrScaleDownBehaviorTerminateAtInstanceHour,
        EmrScaleDownBehaviorTerminateAtTaskCompletion,
    ],
)

EmrRepoUpgradeOnBootSecurity = EnumValue('SECURITY')
EmrRepoUpgradeOnBootNone = EnumValue('NONE')
EmrRepoUpgradeOnBoot = Enum(
    name='EmrRepoUpgradeOnBoot',
    enum_values=[EmrRepoUpgradeOnBootSecurity, EmrRepoUpgradeOnBootNone],
)

EmrMarketOnDemand = EnumValue('ON_DEMAND')
EmrMarketSpot = EnumValue('SPOT')
EmrMarket = Enum(name='EmrMarket', enum_values=[EmrMarketOnDemand, EmrMarketSpot])


EmrInstanceRoleMaster = EnumValue('MASTER')
EmrInstanceRoleCore = EnumValue('CORE')
EmrInstanceRoleTask = EnumValue('TASK')
EmrInstanceRole = Enum(
    name='EmrInstanceRole',
    enum_values=[EmrInstanceRoleMaster, EmrInstanceRoleCore, EmrInstanceRoleTask],
)
