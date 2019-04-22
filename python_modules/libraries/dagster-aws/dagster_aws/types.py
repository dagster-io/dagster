from dagster import Enum, EnumValue

from dagster.core.types.runtime import Stringish
from dagster.utils import safe_isfile


class FileExistsAtPath(Stringish):
    def __init__(self):
        super(FileExistsAtPath, self).__init__(description='A path at which a file actually exists')

    def coerce_runtime_value(self, value):
        value = super(FileExistsAtPath, self).coerce_runtime_value(value)
        return self.throw_if_false(safe_isfile, value)


EbsVolumeTypeGP2 = EnumValue('gp2')
EbsVolumeTypeIO1 = EnumValue('io1')
EbsVolumeTypeStandard = EnumValue('standard')
EbsVolumeType = Enum(
    name='EbsVolumeType', enum_values=[EbsVolumeTypeGP2, EbsVolumeTypeIO1, EbsVolumeTypeStandard]
)

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

EmrAdjustmentTypeChangeInCapacity = EnumValue('CHANGE_IN_CAPACITY')
EmrAdjustmentTypePercentChangeInCapacity = EnumValue('PERCENT_CHANGE_IN_CAPACITY')
EmrAdjustmentTypeExactCapacity = EnumValue('EXACT_CAPACITY')
EmrAdjustmentType = Enum(
    name='EmrAdjustmentType',
    enum_values=[
        EmrAdjustmentTypeChangeInCapacity,
        EmrAdjustmentTypePercentChangeInCapacity,
        EmrAdjustmentTypeExactCapacity,
    ],
)

EmrComparisonOperatorGreaterThanOrEqual = EnumValue('GREATER_THAN_OR_EQUAL')
EmrComparisonOperatorGreaterThan = EnumValue('GREATER_THAN')
EmrComparisonOperatorLessThan = EnumValue('LESS_THAN')
EmrComparisonOperatorLessThanOrEqual = EnumValue('LESS_THAN_OR_EQUAL')
EmrComparisonOperator = Enum(
    name='EmrComparisonOperator',
    enum_values=[
        EmrComparisonOperatorGreaterThanOrEqual,
        EmrComparisonOperatorGreaterThan,
        EmrComparisonOperatorLessThan,
        EmrComparisonOperatorLessThanOrEqual,
    ],
)

EmrInstanceRoleMaster = EnumValue('MASTER')
EmrInstanceRoleCore = EnumValue('CORE')
EmrInstanceRoleTask = EnumValue('TASK')
EmrInstanceRole = Enum(
    name='EmrInstanceRole',
    enum_values=[EmrInstanceRoleMaster, EmrInstanceRoleCore, EmrInstanceRoleTask],
)

EmrMarketOnDemand = EnumValue('ON_DEMAND')
EmrMarketSpot = EnumValue('SPOT')
EmrMarket = Enum(name='EmrMarket', enum_values=[EmrMarketOnDemand, EmrMarketSpot])

EmrRepoUpgradeOnBootSecurity = EnumValue('SECURITY')
EmrRepoUpgradeOnBootNone = EnumValue('NONE')
EmrRepoUpgradeOnBoot = Enum(
    name='EmrRepoUpgradeOnBoot',
    enum_values=[EmrRepoUpgradeOnBootSecurity, EmrRepoUpgradeOnBootNone],
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

EmrStatisticSampleCount = EnumValue('SAMPLE_COUNT')
EmrStatisticAverage = EnumValue('AVERAGE')
EmrStatisticSum = EnumValue('SUM')
EmrStatisticMinimum = EnumValue('MINIMUM')
EmrStatisticMaximum = EnumValue('MAXIMUM')
EmrStatistic = Enum(
    name='EmrStatistic',
    enum_values=[
        EmrStatisticSampleCount,
        EmrStatisticAverage,
        EmrStatisticSum,
        EmrStatisticMinimum,
        EmrStatisticMaximum,
    ],
)
EmrSupportedProductsMapRM3 = EnumValue('mapr-m3')
EmrSupportedProductsMapRM5 = EnumValue('mapr-m5')
EmrSupportedProducts = Enum(
    name='EmrSupportedProducts',
    enum_values=[EmrSupportedProductsMapRM3, EmrSupportedProductsMapRM5],
)

EmrTimeoutActionSwitchToOnDemand = EnumValue('SWITCH_TO_ON_DEMAND')
EmrTimeoutActionTerminateCluster = EnumValue('TERMINATE_CLUSTER')
EmrTimeoutAction = Enum(
    name='EmrTimeoutAction',
    enum_values=[EmrTimeoutActionSwitchToOnDemand, EmrTimeoutActionTerminateCluster],
)


EmrUnitNone = EnumValue('NONE')
EmrUnitSeconds = EnumValue('SECONDS')
EmrUnitMicroseconds = EnumValue('MICRO_SECONDS')
EmrUnitMilliseconds = EnumValue('MILLI_SECONDS')
EmrUnitBytes = EnumValue('BYTES')
EmrUnitKilobytes = EnumValue('KILO_BYTES')
EmrUnitMegabytes = EnumValue('MEGA_BYTES')
EmrUnitGigabytes = EnumValue('GIGA_BYTES')
EmrUnitTerabytes = EnumValue('TERA_BYTES')
EmrUnitBits = EnumValue('BITS')
EmrUnitKilobits = EnumValue('KILO_BITS')
EmrUnitMegabits = EnumValue('MEGA_BITS')
EmrUnitGigabits = EnumValue('GIGA_BITS')
EmrUnitTerabits = EnumValue('TERA_BITS')
EmrUnitPercent = EnumValue('PERCENT')
EmrUnitCount = EnumValue('COUNT')
EmrUnitBytesPerSecond = EnumValue('BYTES_PER_SECOND')
EmrUnitKilobytesPerSecond = EnumValue('KILO_BYTES_PER_SECOND')
EmrUnitMegabytesPerSecond = EnumValue('MEGA_BYTES_PER_SECOND')
EmrUnitGigabytesPerSecond = EnumValue('GIGA_BYTES_PER_SECOND')
EmrUnitTerabytesPerSecond = EnumValue('TERA_BYTES_PER_SECOND')
EmrUnitBitsPerSecond = EnumValue('BITS_PER_SECOND')
EmrUnitKilobitsPerSecond = EnumValue('KILO_BITS_PER_SECOND')
EmrUnitMegabitsPerSecond = EnumValue('MEGA_BITS_PER_SECOND')
EmrUnitGigabitsPerSecond = EnumValue('GIGA_BITS_PER_SECOND')
EmrUnitTerabitsPerSecond = EnumValue('TERA_BITS_PER_SECOND')
EmrUnitCountPerSecond = EnumValue('COUNT_PER_SECOND')
EmrUnit = Enum(
    name='EmrUnit',
    enum_values=[
        EmrUnitNone,
        EmrUnitSeconds,
        EmrUnitMicroseconds,
        EmrUnitMilliseconds,
        EmrUnitBytes,
        EmrUnitKilobytes,
        EmrUnitMegabytes,
        EmrUnitGigabytes,
        EmrUnitTerabytes,
        EmrUnitBits,
        EmrUnitKilobits,
        EmrUnitMegabits,
        EmrUnitGigabits,
        EmrUnitTerabits,
        EmrUnitPercent,
        EmrUnitCount,
        EmrUnitBytesPerSecond,
        EmrUnitKilobytesPerSecond,
        EmrUnitMegabytesPerSecond,
        EmrUnitGigabytesPerSecond,
        EmrUnitTerabytesPerSecond,
        EmrUnitBitsPerSecond,
        EmrUnitKilobitsPerSecond,
        EmrUnitMegabitsPerSecond,
        EmrUnitGigabitsPerSecond,
        EmrUnitTerabitsPerSecond,
        EmrUnitCountPerSecond,
    ],
)
