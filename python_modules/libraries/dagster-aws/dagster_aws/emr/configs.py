from dagster import Bool, Field, Float, Int, Permissive, Shape, String

from dagster_aws.emr.types import (
    EbsVolumeType,
    EmrActionOnFailure,
    EmrAdjustmentType,
    EmrComparisonOperator,
    EmrInstanceRole,
    EmrMarket,
    EmrRepoUpgradeOnBoot,
    EmrScaleDownBehavior,
    EmrStatistic,
    EmrSupportedProducts,
    EmrTimeoutAction,
    EmrUnit,
)


def _define_configurations():
    return Field(
        [
            Shape(
                fields={
                    "Classification": Field(
                        String,
                        description="The classification within a configuration.",
                        is_required=False,
                    ),
                    "Configurations": Field(
                        [Permissive()],
                        description="""A list of additional configurations to apply within a
                                configuration object.""",
                        is_required=False,
                    ),
                    "Properties": Field(
                        Permissive(),
                        description="""A set of properties specified within a configuration
                                classification.""",
                        is_required=False,
                    ),
                }
            )
        ],
        description="""For Amazon EMR releases 4.0 and later. The list of configurations supplied
        for the EMR cluster you are creating.

        An optional configuration specification to be used when provisioning cluster instances,
        which can include configurations for applications and software bundled with Amazon EMR. A
        configuration consists of a classification, properties, and optional nested configurations.
        A classification refers to an application-specific configuration file. Properties are the
        settings you want to change in that file. For more information, see the EMR Configuring
        Applications guide.""",
        is_required=False,
    )


def _define_steps():
    name = Field(String, description="The name of the step.", is_required=True)

    actionOnFailure = Field(
        EmrActionOnFailure,
        description="""The action to take when the cluster step fails. Possible values are
        TERMINATE_CLUSTER, CANCEL_AND_WAIT, and CONTINUE. TERMINATE_JOB_FLOW is provided for
        backward compatibility. We recommend using TERMINATE_CLUSTER instead.""",
        is_required=False,
    )

    hadoopJarStep = Field(
        Shape(
            fields={
                "Properties": Field(
                    [Shape(fields={"Key": Field(String), "Value": Field(String)})],
                    description="""A list of Java properties that are set when the step runs. You
                    can use these properties to pass key value pairs to your main function.""",
                    is_required=False,
                ),
                "Jar": Field(
                    String,
                    description="A path to a JAR file run during the step.",
                    is_required=True,
                ),
                "MainClass": Field(
                    String,
                    description="""The name of the main class in the specified Java file. If not
                    specified, the JAR file should specify a Main-Class in its manifest file.""",
                    is_required=False,
                ),
                "Args": Field(
                    [String],
                    description="""A list of command line arguments passed to the JAR file's main
                    function when executed.""",
                    is_required=False,
                ),
            }
        ),
        description="The JAR file used for the step.",
    )

    return Field(
        [
            Shape(
                fields={
                    "Name": name,
                    "ActionOnFailure": actionOnFailure,
                    "HadoopJarStep": hadoopJarStep,
                }
            )
        ],
        description="A list of steps to run.",
    )


def _define_bootstrap_actions():
    name = Field(String, description="The name of the bootstrap action.", is_required=True)

    path = Field(
        String,
        description="""Location of the script to run during a bootstrap action. Can be either a
        location in Amazon S3 or on a local file system.""",
        is_required=True,
    )

    args = Field(
        [String],
        description="A list of command line arguments to pass to the bootstrap action script.",
        is_required=False,
    )

    bootstrap_action = Shape(
        fields={
            "Name": name,
            "ScriptBootstrapAction": Field(
                Shape(fields={"Path": path, "Args": args}),
                description="The script run by the bootstrap action.",
                is_required=True,
            ),
        }
    )

    return Field(
        [bootstrap_action],
        description="""A list of bootstrap actions to run before Hadoop starts on the cluster
        nodes.""",
        is_required=False,
    )


def _define_ebs_configuration():
    volume_specification = Field(
        Shape(
            fields={
                "VolumeType": Field(
                    EbsVolumeType,
                    description="""The volume type. Volume types supported are gp2, io1,
                    standard.""",
                    is_required=True,
                ),
                "Iops": Field(
                    Int,
                    description="""The number of I/O operations per second (IOPS) that the volume
                    supports.""",
                    is_required=False,
                ),
                "SizeInGB": Field(
                    Int,
                    description="""The volume size, in gibibytes (GiB). This can be a number from
                    1 - 1024. If the volume type is EBS-optimized, the minimum value is 10.""",
                    is_required=True,
                ),
            }
        ),
        description="""EBS volume specifications such as volume type, IOPS, and size (GiB) that will
        be requested for the EBS volume attached to an EC2 instance in the cluster.""",
        is_required=True,
    )

    volumes_per_instance = Field(
        Int,
        description="""Number of EBS volumes with a specific volume configuration that will be
        associated with every instance in the instance group""",
        is_required=False,
    )

    return Field(
        Shape(
            fields={
                "EbsBlockDeviceConfigs": Field(
                    [
                        Shape(
                            fields={
                                "VolumeSpecification": volume_specification,
                                "VolumesPerInstance": volumes_per_instance,
                            }
                        )
                    ],
                    description="""An array of Amazon EBS volume specifications attached to a
                    cluster instance.""",
                    is_required=False,
                ),
                "EbsOptimized": Field(
                    Bool,
                    description="Indicates whether an Amazon EBS volume is EBS-optimized.",
                    is_required=False,
                ),
            }
        ),
        description="""EBS configurations that will be attached to each EC2 instance in the
        instance group.""",
        is_required=False,
    )


def _define_auto_scaling_policy():
    simple_scaling_policy_configuration = Field(
        Shape(
            fields={
                "AdjustmentType": Field(
                    EmrAdjustmentType,
                    description="""The way in which EC2 instances are added (if ScalingAdjustment
                    is a positive number) or terminated (if ScalingAdjustment is a negative number)
                    each time the scaling activity is triggered. CHANGE_IN_CAPACITY is the default.
                    CHANGE_IN_CAPACITY indicates that the EC2 instance count increments or
                    decrements by ScalingAdjustment , which should be expressed as an integer.
                    PERCENT_CHANGE_IN_CAPACITY indicates the instance count increments or decrements
                    by the percentage specified by ScalingAdjustment , which should be expressed as
                    an integer. For example, 20 indicates an increase in 20% increments of cluster
                    capacity. EXACT_CAPACITY indicates the scaling activity results in an instance
                    group with the number of EC2 instances specified by ScalingAdjustment , which
                    should be expressed as a positive integer.""",
                    is_required=False,
                ),
                "ScalingAdjustment": Field(
                    Int,
                    description="""The amount by which to scale in or scale out, based on the
                    specified AdjustmentType . A positive value adds to the instance group's EC2
                    instance count while a negative number removes instances. If AdjustmentType is
                    set to EXACT_CAPACITY , the number should only be a positive integer. If
                    AdjustmentType is set to PERCENT_CHANGE_IN_CAPACITY , the value should express
                    the percentage as an integer. For example, -20 indicates a decrease in 20%
                    increments of cluster capacity.""",
                    is_required=True,
                ),
                "CoolDown": Field(
                    Int,
                    description="""The amount of time, in seconds, after a scaling activity
                    completes before any further trigger-related scaling activities can start. The
                    default value is 0.""",
                    is_required=False,
                ),
            }
        ),
        description="""The type of adjustment the automatic scaling activity makes when
                    triggered, and the periodicity of the adjustment.""",
        is_required=True,
    )

    action = Field(
        Shape(
            fields={
                "Market": Field(
                    EmrMarket,
                    description="""Not available for instance groups. Instance groups use the market
                    type specified for the group.""",
                    is_required=False,
                ),
                "SimpleScalingPolicyConfiguration": simple_scaling_policy_configuration,
            }
        ),
        description="The conditions that trigger an automatic scaling activity.",
        is_required=True,
    )

    dimensions = Field(
        [
            Shape(
                fields={
                    "Key": Field(String, description="The dimension name.", is_required=True),
                    "Value": Field(String, description="The dimension value.", is_required=False),
                }
            )
        ],
        description="""A CloudWatch metric dimension.""",
        is_required=False,
    )

    trigger = Field(
        Shape(
            fields={
                "CloudWatchAlarmDefinition": Field(
                    Shape(
                        fields={
                            "ComparisonOperator": Field(
                                EmrComparisonOperator,
                                description="""Determines how the metric specified by MetricName is
                                compared to the value specified by Threshold.""",
                                is_required=True,
                            ),
                            "EvaluationPeriods": Field(
                                Int,
                                description="""The number of periods, expressed in seconds using
                                Period, during which the alarm condition must exist before the alarm
                                triggers automatic scaling activity. The default value is 1.""",
                                is_required=False,
                            ),
                            "MetricName": Field(
                                String,
                                description="""The name of the CloudWatch metric that is watched to
                                determine an alarm condition.""",
                                is_required=False,
                            ),
                            "Namespace": Field(
                                String,
                                description="""The namespace for the CloudWatch metric. The default
                                is AWS/ElasticMapReduce.""",
                                is_required=False,
                            ),
                            "Period": Field(
                                Int,
                                description="""The period, in seconds, over which the statistic is
                                applied. EMR CloudWatch metrics are emitted every five minutes (300
                                seconds), so if an EMR CloudWatch metric is specified, specify
                                300.""",
                                is_required=True,
                            ),
                            "Statistic": Field(
                                EmrStatistic,
                                description="""The statistic to apply to the metric associated with
                                the alarm. The default is AVERAGE.""",
                                is_required=False,
                            ),
                            "Threshold": Field(
                                Float,
                                description="""The value against which the specified statistic is
                                compared.""",
                                is_required=True,
                            ),
                            "Unit": Field(
                                EmrUnit,
                                description="""The unit of measure associated with the CloudWatch
                                metric being watched. The value specified for Unit must correspond
                                to the units specified in the CloudWatch metric.""",
                                is_required=False,
                            ),
                            "Dimensions": dimensions,
                        }
                    ),
                    description="""The definition of a CloudWatch metric alarm. When the defined
                    alarm conditions are met along with other trigger parameters, scaling activity
                    begins.""",
                    is_required=True,
                )
            }
        ),
        description="""The CloudWatch alarm definition that determines when automatic scaling
        activity is triggered.""",
        is_required=True,
    )

    return Field(
        Shape(
            fields={
                "Constraints": Field(
                    Shape(
                        fields={
                            "MinCapacity": Field(
                                Int,
                                description="""The lower boundary of EC2 instances in an instance
                                group below which scaling activities are not allowed to shrink.
                                Scale-in activities will not terminate instances below this
                                boundary.""",
                                is_required=True,
                            ),
                            "MaxCapacity": Field(
                                Int,
                                description="""The upper boundary of EC2 instances in an instance
                                group beyond which scaling activities are not allowed to grow.
                                Scale-out activities will not add instances beyond this
                                boundary.""",
                                is_required=True,
                            ),
                        }
                    ),
                    description="""The upper and lower EC2 instance limits for an automatic scaling
                    policy. Automatic scaling activity will not cause an instance group to grow
                    above or below these limits.""",
                    is_required=True,
                ),
                "Rules": Field(
                    [
                        Shape(
                            fields={
                                "Name": Field(
                                    String,
                                    description="""The name used to identify an automatic
                                        scaling rule. Rule names must be unique within a scaling
                                        policy.""",
                                ),
                                "Description": Field(
                                    String,
                                    description="""A friendly, more verbose description of the
                                        automatic scaling rule.""",
                                ),
                                "Action": action,
                                "Trigger": trigger,
                            }
                        )
                    ],
                    description="""A scale-in or scale-out rule that defines scaling activity,
                    including the CloudWatch metric alarm that triggers activity, how EC2 instances
                    are added or removed, and the periodicity of adjustments. The automatic scaling
                    policy for an instance group can comprise one or more automatic scaling
                    rules.""",
                    is_required=True,
                ),
            }
        ),
        description="""An automatic scaling policy for a core instance group or task instance group
        in an Amazon EMR cluster. The automatic scaling policy defines how an instance group
        dynamically adds and terminates EC2 instances in response to the value of a CloudWatch
        metric. See the EMR PutAutoScalingPolicy docs.
        """,
        is_required=False,
    )


def _define_instance_groups():
    return Field(
        [
            Shape(
                fields={
                    "Name": Field(
                        String,
                        description="Friendly name given to the instance group.",
                        is_required=False,
                    ),
                    "Market": Field(
                        EmrMarket,
                        description="""Market type of the EC2 instances used to create a cluster
                            node.""",
                        is_required=False,
                    ),
                    "InstanceRole": Field(
                        EmrInstanceRole,
                        description="The role of the instance group in the cluster.",
                        is_required=True,
                    ),
                    "BidPrice": Field(
                        String,
                        description="""The maximum Spot price your are willing to pay for EC2
                            instances.

                            An optional, nullable field that applies if the MarketType for the
                            instance group is specified as SPOT . Specify the maximum spot price in
                            USD. If the value is NULL and SPOT is specified, the maximum Spot price
                            is set equal to the On-Demand price.""",
                        is_required=False,
                    ),
                    "InstanceType": Field(
                        String,
                        description="""The EC2 instance type for all instances in the instance
                            group.""",
                        is_required=True,
                    ),
                    "InstanceCount": Field(
                        Int,
                        description="Target number of instances for the instance group.",
                        is_required=True,
                    ),
                    "Configurations": _define_configurations(),
                    "EbsConfiguration": _define_ebs_configuration(),
                    "AutoScalingPolicy": _define_auto_scaling_policy(),
                }
            )
        ],
        description="Configuration for the instance groups in a cluster.",
        is_required=False,
    )


def _define_instance_fleets():
    target_on_demand_capacity = Field(
        Int,
        description="""The target capacity of On-Demand units for the instance fleet, which
        determines how many On-Demand instances to provision. When the instance fleet launches,
        Amazon EMR tries to provision On-Demand instances as specified by InstanceTypeConfig. Each
        instance configuration has a specified WeightedCapacity. When an On-Demand instance is
        provisioned, the WeightedCapacity units count toward the target capacity. Amazon EMR
        provisions instances until the target capacity is totally fulfilled, even if this results
        in an overage. For example, if there are 2 units remaining to fulfill capacity, and Amazon
        EMR can only provision an instance with a WeightedCapacity of 5 units, the instance is
        provisioned, and the target capacity is exceeded by 3 units.

        Note: If not specified or set to 0, only Spot instances are provisioned for the instance
        fleet using TargetSpotCapacity. At least one of TargetSpotCapacity and
        TargetOnDemandCapacity should be greater than 0. For a master instance fleet, only one of
        TargetSpotCapacity and TargetOnDemandCapacity can be specified, and its value must be 1.
        """,
        is_required=True,
    )

    target_spot_capacity = Field(
        Int,
        description="""The target capacity of Spot units for the instance fleet, which determines
        how many Spot instances to provision. When the instance fleet launches, Amazon EMR tries to
        provision Spot instances as specified by InstanceTypeConfig . Each instance configuration
        has a specified WeightedCapacity . When a Spot instance is provisioned, the WeightedCapacity
        units count toward the target capacity. Amazon EMR provisions instances until the target
        capacity is totally fulfilled, even if this results in an overage. For example, if there are
        2 units remaining to fulfill capacity, and Amazon EMR can only provision an instance with a
        WeightedCapacity of 5 units, the instance is provisioned, and the target capacity is
        exceeded by 3 units.

        Note: If not specified or set to 0, only On-Demand instances are provisioned for the
        instance fleet. At least one of TargetSpotCapacity and TargetOnDemandCapacity should be
        greater than 0. For a master instance fleet, only one of TargetSpotCapacity and
        TargetOnDemandCapacity can be specified, and its value must be 1.
        """,
        is_required=False,
    )

    instance_type_configs = Field(
        [
            Shape(
                fields={
                    "InstanceType": Field(
                        String,
                        description="An EC2 instance type, such as m3.xlarge.",
                        is_required=True,
                    ),
                    "WeightedCapacity": Field(
                        Int,
                        description="""The number of units that a provisioned instance of this
                            type provides toward fulfilling the target capacities defined in
                            InstanceFleetConfig. This value is 1 for a master instance fleet, and
                            must be 1 or greater for core and task instance fleets. Defaults to 1
                            if not specified.""",
                        is_required=False,
                    ),
                    "BidPrice": Field(
                        String,
                        description="""The bid price for each EC2 Spot instance type as defined
                            by InstanceType. Expressed in USD. If neither BidPrice nor
                            BidPriceAsPercentageOfOnDemandPrice is provided,
                            BidPriceAsPercentageOfOnDemandPrice defaults to 100%.""",
                    ),
                    "BidPriceAsPercentageOfOnDemandPrice": Field(
                        Float,
                        description="""The bid price, as a percentage of On-Demand price, for
                            each EC2 Spot instance as defined by InstanceType . Expressed as a
                            number (for example, 20 specifies 20%). If neither BidPrice nor
                            BidPriceAsPercentageOfOnDemandPrice is provided,
                            BidPriceAsPercentageOfOnDemandPrice defaults to 100%.""",
                        is_required=False,
                    ),
                    "EbsConfiguration": _define_ebs_configuration(),
                    "Configurations": _define_configurations(),
                }
            )
        ],
        description="""An instance type configuration for each instance type in an instance fleet,
        which determines the EC2 instances Amazon EMR attempts to provision to fulfill On-Demand and
        Spot target capacities. There can be a maximum of 5 instance type configurations in a
        fleet.""",
        is_required=False,
    )

    launch_specifications = Field(
        Shape(
            fields={
                "SpotSpecification": Field(
                    Shape(
                        fields={
                            "TimeoutDurationMinutes": Field(
                                Int,
                                description="""The spot provisioning timeout period in minutes. If
                                Spot instances are not provisioned within this time period, the
                                TimeOutAction is taken. Minimum value is 5 and maximum value is
                                1440. The timeout applies only during initial provisioning, when the
                                cluster is first created.""",
                                is_required=True,
                            ),
                            "TimeoutAction": Field(
                                EmrTimeoutAction,
                                description="""The action to take when TargetSpotCapacity has not
                                been fulfilled when the TimeoutDurationMinutes has expired; that is,
                                when all Spot instances could not be provisioned within the Spot
                                provisioning timeout. Valid values are TERMINATE_CLUSTER and
                                SWITCH_TO_ON_DEMAND. SWITCH_TO_ON_DEMAND specifies that if no Spot
                                instances are available, On-Demand Instances should be provisioned
                                to fulfill any remaining Spot capacity.""",
                                is_required=True,
                            ),
                            "BlockDurationMinutes": Field(
                                Int,
                                description="""The defined duration for Spot instances (also known
                                as Spot blocks) in minutes. When specified, the Spot instance does
                                not terminate before the defined duration expires, and defined
                                duration pricing for Spot instances applies. Valid values are 60,
                                120, 180, 240, 300, or 360. The duration period starts as soon as a
                                Spot instance receives its instance ID. At the end of the duration,
                                Amazon EC2 marks the Spot instance for termination and provides a
                                Spot instance termination notice, which gives the instance a
                                two-minute warning before it terminates.""",
                                is_required=False,
                            ),
                        }
                    ),
                    description="""The launch specification for Spot instances in the fleet, which
                    determines the defined duration and provisioning timeout behavior.""",
                    is_required=True,
                )
            }
        ),
        description="The launch specification for the instance fleet.",
        is_required=False,
    )

    return Field(
        [
            Shape(
                fields={
                    "Name": Field(
                        String,
                        description="The friendly name of the instance fleet.",
                        is_required=False,
                    ),
                    "InstanceFleetType": Field(
                        EmrInstanceRole,
                        description="""The node type that the instance fleet hosts. Valid values
                            are MASTER,CORE,and TASK.""",
                    ),
                    "TargetOnDemandCapacity": target_on_demand_capacity,
                    "TargetSpotCapacity": target_spot_capacity,
                    "InstanceTypeConfigs": instance_type_configs,
                    "LaunchSpecifications": launch_specifications,
                }
            )
        ],
        description="""Describes the EC2 instances and instance configurations for clusters that use
        the instance fleet configuration.""",
        is_required=False,
    )


def define_emr_run_job_flow_config():
    name = Field(String, description="The name of the job flow.", is_required=True)

    log_uri = Field(
        String,
        description="""The location in Amazon S3 to write the log files of the job flow. If a value
        is not provided, logs are not created.""",
        is_required=False,
    )

    additional_info = Field(
        String, description="A JSON string for selecting additional features.", is_required=False
    )

    ami_version = Field(
        String,
        description="""Applies only to Amazon EMR AMI versions 3.x and 2.x. For Amazon EMR releases
        4.0 and later, ReleaseLabel is used. To specify a custom AMI, use CustomAmiID.""",
        is_required=False,
    )

    release_label = Field(
        String,
        description="""The Amazon EMR release label, which determines the version of open-source
        application packages installed on the cluster. Release labels are in the form emr-x.x.x,
        where x.x.x is an Amazon EMR release version, for example, emr-5.14.0 . For more information
        about Amazon EMR release versions and included application versions and features, see
        https://docs.aws.amazon.com/emr/latest/ReleaseGuide/. The release label applies only to
        Amazon EMR releases versions 4.x and later. Earlier versions use AmiVersion.""",
        is_required=False,
    )

    instances = Field(
        Shape(
            fields={
                "MasterInstanceType": Field(
                    String,
                    description="The EC2 instance type of the master node.",
                    is_required=False,
                ),
                "SlaveInstanceType": Field(
                    String,
                    description="The EC2 instance type of the core and task nodes.",
                    is_required=False,
                ),
                "InstanceCount": Field(
                    Int,
                    description="The number of EC2 instances in the cluster.",
                    is_required=False,
                ),
                "InstanceGroups": _define_instance_groups(),
                "InstanceFleets": _define_instance_fleets(),
                "Ec2KeyName": Field(
                    String,
                    description='''The name of the EC2 key pair that can be used to ssh to the
                    master node as the user called "hadoop."''',
                    is_required=False,
                ),
                "Placement": Field(
                    Shape(
                        fields={
                            "AvailabilityZone": Field(
                                String,
                                description="""The Amazon EC2 Availability Zone for the cluster.
                                AvailabilityZone is used for uniform instance groups, while
                                AvailabilityZones (plural) is used for instance fleets.""",
                                is_required=False,
                            ),
                            "AvailabilityZones": Field(
                                [String],
                                description="""When multiple Availability Zones are specified,
                                Amazon EMR evaluates them and launches instances in the optimal
                                Availability Zone. AvailabilityZones is used for instance fleets,
                                while AvailabilityZone (singular) is used for uniform instance
                                groups.""",
                                is_required=False,
                            ),
                        }
                    ),
                    description="The Availability Zone in which the cluster runs.",
                    is_required=False,
                ),
                "KeepJobFlowAliveWhenNoSteps": Field(
                    Bool,
                    description="""Specifies whether the cluster should remain available after
                    completing all steps.""",
                    is_required=False,
                ),
                "TerminationProtected": Field(
                    Bool,
                    description="""Specifies whether to lock the cluster to prevent the Amazon EC2
                    instances from being terminated by API call, user intervention, or in the event
                    of a job-flow error.""",
                    is_required=False,
                ),
                "HadoopVersion": Field(
                    String,
                    description="""Applies only to Amazon EMR release versions earlier than 4.0. The
                    Hadoop version for the cluster. Valid inputs are "0.18" (deprecated), "0.20"
                    (deprecated), "0.20.205" (deprecated), "1.0.3", "2.2.0", or "2.4.0". If you do
                    not set this value, the default of 0.18 is used, unless the AmiVersion parameter
                    is set in the RunJobFlow call, in which case the default version of Hadoop for
                    that AMI version is used.""",
                    is_required=False,
                ),
                "Ec2SubnetId": Field(
                    String,
                    description="""Applies to clusters that use the uniform instance group
                    configuration. To launch the cluster in Amazon Virtual Private Cloud (Amazon
                    VPC), set this parameter to the identifier of the Amazon VPC subnet where you
                    want the cluster to launch. If you do not specify this value, the cluster
                    launches in the normal Amazon Web Services cloud, outside of an Amazon VPC, if
                    the account launching the cluster supports EC2 Classic networks in the region
                    where the cluster launches.
                    Amazon VPC currently does not support cluster compute quadruple extra large
                    (cc1.4xlarge) instances. Thus you cannot specify the cc1.4xlarge instance type
                    for clusters launched in an Amazon VPC.""",
                    is_required=False,
                ),
                "Ec2SubnetIds": Field(
                    [String],
                    description="""Applies to clusters that use the instance fleet configuration.
                    When multiple EC2 subnet IDs are specified, Amazon EMR evaluates them and
                    launches instances in the optimal subnet.""",
                    is_required=False,
                ),
                "EmrManagedMasterSecurityGroup": Field(
                    String,
                    description="""The identifier of the Amazon EC2 security group for the master
                    node.""",
                    is_required=False,
                ),
                "EmrManagedSlaveSecurityGroup": Field(
                    String,
                    description="""The identifier of the Amazon EC2 security group for the core and
                    task nodes.""",
                    is_required=False,
                ),
                "ServiceAccessSecurityGroup": Field(
                    String,
                    description="""The identifier of the Amazon EC2 security group for the Amazon
                    EMR service to access clusters in VPC private subnets.""",
                    is_required=False,
                ),
                "AdditionalMasterSecurityGroups": Field(
                    [String],
                    description="""A list of additional Amazon EC2 security group IDs for the master
                    node.""",
                    is_required=False,
                ),
                "AdditionalSlaveSecurityGroups": Field(
                    [String],
                    description="""A list of additional Amazon EC2 security group IDs for the core
                    and task nodes.""",
                    is_required=False,
                ),
            }
        ),
        description="A specification of the number and type of Amazon EC2 instances.",
        is_required=True,
    )

    supported_products = Field(
        [EmrSupportedProducts],
        description="""A list of strings that indicates third-party software to use. For
                    more information, see the Amazon EMR Developer Guide. Currently supported
                    values are:
                        - "mapr-m3" - launch the job flow using MapR M3 Edition.
                        - "mapr-m5" - launch the job flow using MapR M5 Edition.
                    """,
        is_required=False,
    )

    new_supported_products = Field(
        [
            Shape(
                fields={
                    "Name": Field(String, is_required=True),
                    "Args": Field([String], description="The list of user-supplied arguments."),
                }
            )
        ],
        description="""
        The list of supported product configurations which allow user-supplied arguments. EMR
        accepts these arguments and forwards them to the corresponding installation script as
        bootstrap action arguments.

        A list of strings that indicates third-party software to use with the job flow that accepts
        a user argument list. EMR accepts and forwards the argument list to the corresponding
        installation script as bootstrap action arguments. For more information, see "Launch a Job
        Flow on the MapR Distribution for Hadoop" in the Amazon EMR Developer Guide.

        Supported values are:
        - "mapr-m3" - launch the cluster using MapR M3 Edition.
        - "mapr-m5" - launch the cluster using MapR M5 Edition.
        - "mapr" with the user arguments specifying "--edition,m3" or "--edition,m5" - launch the
            job flow using MapR M3 or M5 Edition respectively.
        - "mapr-m7" - launch the cluster using MapR M7 Edition.
        - "hunk" - launch the cluster with the Hunk Big Data Analtics Platform.
        - "hue"- launch the cluster with Hue installed.
        - "spark" - launch the cluster with Apache Spark installed.
        - "ganglia" - launch the cluster with the Ganglia Monitoring System installed.""",
        is_required=False,
    )

    applications = Field(
        [
            Shape(
                fields={
                    "Name": Field(
                        String, description="The name of the application.", is_required=True
                    ),
                    "Version": Field(
                        String, description="The version of the application.", is_required=False
                    ),
                    "Args": Field(
                        [String],
                        description="Arguments for Amazon EMR to pass to the application.",
                        is_required=False,
                    ),
                    "AdditionalInfo": Field(
                        Permissive(),
                        description="""This option is for advanced users only. This is meta
                            information about third-party applications that third-party vendors use
                            for testing purposes.""",
                        is_required=False,
                    ),
                }
            )
        ],
        description="""Applies to Amazon EMR releases 4.0 and later. A case-insensitive list of
        applications for Amazon EMR to install and configure when launching the cluster. For a list
        of applications available for each Amazon EMR release version, see the Amazon EMR Release
        Guide.

        With Amazon EMR release version 4.0 and later, the only accepted parameter is the
        application name. To pass arguments to applications, you use configuration classifications
        specified using configuration JSON objects. For more information, see the EMR Configuring
        Applications guide.

        With earlier Amazon EMR releases, the application is any Amazon or third-party software that
        you can add to the cluster. This structure contains a list of strings that indicates the
        software to use with the cluster and accepts a user argument list. Amazon EMR accepts and
        forwards the argument list to the corresponding installation script as bootstrap action
        argument.""",
        is_required=False,
    )

    visible_to_all_users = Field(
        Bool,
        description="""Whether the cluster is visible to all IAM users of the AWS account associated
        with the cluster. If this value is set to True, all IAM users of that AWS account can view
        and (if they have the proper policy permissions set) manage the cluster. If it is set to
        False, only the IAM user that created the cluster can view and manage it.""",
        is_required=False,
        default_value=True,
    )

    job_flow_role = Field(
        String,
        description="""Also called instance profile and EC2 role. An IAM role for an EMR cluster.
        The EC2 instances of the cluster assume this role. The default role is EMR_EC2_DefaultRole.
        In order to use the default role, you must have already created it using the CLI or console.
        """,
        is_required=False,
    )

    service_role = Field(
        String,
        description="""The IAM role that will be assumed by the Amazon EMR service to access AWS
        resources on your behalf.""",
        is_required=False,
    )

    tags = Field(
        [
            Shape(
                fields={
                    "Key": Field(
                        String,
                        description="""A user-defined key, which is the minimum required information
                        for a valid tag. For more information, see the EMR Tag guide.""",
                        is_required=True,
                    ),
                    "Value": Field(
                        String,
                        description="""A user-defined value, which is optional in a tag. For more
                        information, see the EMR Tag Clusters guide.""",
                        is_required=False,
                    ),
                }
            )
        ],
        description="""A list of tags to associate with a cluster and propagate to Amazon EC2
        instances.

        A key/value pair containing user-defined metadata that you can associate with an Amazon EMR
        resource. Tags make it easier to associate clusters in various ways, such as grouping
        clusters to track your Amazon EMR resource allocation costs. For more information, see the
        EMR Tag Clusters guide.""",
        is_required=False,
    )

    security_configuration = Field(
        String,
        description="The name of a security configuration to apply to the cluster.",
        is_required=False,
    )

    auto_scaling_role = Field(
        String,
        description="""An IAM role for automatic scaling policies. The default role is
        EMR_AutoScaling_DefaultRole. The IAM role provides permissions that the automatic scaling
        feature requires to launch and terminate EC2 instances in an instance group.""",
        is_required=False,
    )

    scale_down_behavior = Field(
        EmrScaleDownBehavior,
        description="""Specifies the way that individual Amazon EC2 instances terminate when an
        automatic scale-in activity occurs or an instance group is resized.
        TERMINATE_AT_INSTANCE_HOUR indicates that Amazon EMR terminates nodes at the instance-hour
        boundary, regardless of when the request to terminate the instance was submitted. This
        option is only available with Amazon EMR 5.1.0 and later and is the default for clusters
        created using that version. TERMINATE_AT_TASK_COMPLETION indicates that Amazon EMR
        blacklists and drains tasks from nodes before terminating the Amazon EC2 instances,
        regardless of the instance-hour boundary. With either behavior, Amazon EMR removes the least
        active nodes first and blocks instance termination if it could lead to HDFS corruption.
        TERMINATE_AT_TASK_COMPLETION available only in Amazon EMR version 4.1.0 and later, and is
        the default for versions of Amazon EMR earlier than 5.1.0.""",
        is_required=False,
    )

    custom_ami_id = Field(
        String,
        description="""Available only in Amazon EMR version 5.7.0 and later. The ID of a custom
        Amazon EBS-backed Linux AMI. If specified, Amazon EMR uses this AMI when it launches cluster
        EC2 instances. For more information about custom AMIs in Amazon EMR, see Using a Custom AMI
        in the Amazon EMR Management Guide. If omitted, the cluster uses the base Linux AMI for the
        ReleaseLabel specified. For Amazon EMR versions 2.x and 3.x, use AmiVersion instead.

        For information about creating a custom AMI, see Creating an Amazon EBS-Backed Linux AMI in
        the Amazon Elastic Compute Cloud User Guide for Linux Instances. For information about
        finding an AMI ID, see Finding a Linux AMI.""",
        is_required=False,
    )

    repo_upgrade_on_boot = Field(
        EmrRepoUpgradeOnBoot,
        description="""Applies only when CustomAmiID is used. Specifies which updates from the
        Amazon Linux AMI package repositories to apply automatically when the instance boots using
        the AMI. If omitted, the default is SECURITY , which indicates that only security updates
        are applied. If NONE is specified, no updates are applied, and all updates must be applied
        manually.""",
        is_required=False,
    )

    kerberos_attributes = Field(
        Shape(
            fields={
                "Realm": Field(
                    String,
                    description="""The name of the Kerberos realm to which all nodes in a cluster
                    belong. For example, EC2.INTERNAL.""",
                    is_required=True,
                ),
                "KdcAdminPassword": Field(
                    String,
                    description="""The password used within the cluster for the kadmin service on
                    the cluster-dedicated KDC, which maintains Kerberos principals, password
                    policies, and keytabs for the cluster.""",
                    is_required=True,
                ),
                "CrossRealmTrustPrincipalPassword": Field(
                    String,
                    description="""Required only when establishing a cross-realm trust with a KDC in
                    a different realm. The cross-realm principal password, which must be identical
                    across realms.""",
                    is_required=False,
                ),
                "ADDomainJoinUser": Field(
                    String,
                    description="""Required only when establishing a cross-realm trust with an
                    Active Directory domain. A user with sufficient privileges to join resources to
                    the domain.""",
                    is_required=False,
                ),
                "ADDomainJoinPassword": Field(
                    String,
                    description="""The Active Directory password for ADDomainJoinUser.""",
                    is_required=False,
                ),
            }
        ),
        description="""Attributes for Kerberos configuration when Kerberos authentication is enabled
        using a security configuration. For more information see Use Kerberos Authentication in the
        EMR Management Guide .""",
        is_required=False,
    )

    return Field(
        Shape(
            fields={
                "Name": name,
                "LogUri": log_uri,
                "AdditionalInfo": additional_info,
                "AmiVersion": ami_version,
                "ReleaseLabel": release_label,
                "Instances": instances,
                "Steps": _define_steps(),
                "BootstrapActions": _define_bootstrap_actions(),
                "SupportedProducts": supported_products,
                "NewSupportedProducts": new_supported_products,
                "Applications": applications,
                "Configurations": _define_configurations(),
                "VisibleToAllUsers": visible_to_all_users,
                "JobFlowRole": job_flow_role,
                "ServiceRole": service_role,
                "Tags": tags,
                "SecurityConfiguration": security_configuration,
                "AutoScalingRole": auto_scaling_role,
                "ScaleDownBehavior": scale_down_behavior,
                "CustomAmiId": custom_ami_id,
                "EbsRootVolumeSize": Field(
                    Int,
                    description="""The size, in GiB, of the EBS root device volume of the Linux AMI
                    that is used for each EC2 instance. Available in Amazon EMR version 4.x and
                    later.""",
                    is_required=False,
                ),
                "RepoUpgradeOnBoot": repo_upgrade_on_boot,
                "KerberosAttributes": kerberos_attributes,
            }
        ),
        description="AWS EMR run job flow configuration",
    )
