from dagster import Bool, Dict, Field, Int, List, PermissiveDict, String

from .types import (
    EmrActionOnFailure,
    EmrInstanceRole,
    EmrMarket,
    EmrRepoUpgradeOnBoot,
    EmrScaleDownBehavior,
    EmrSupportedProducts,
)


def _define_configurations():
    return Field(
        List(
            Field(
                Dict(
                    fields={
                        'Classification': Field(
                            String,
                            description='The classification within a configuration.',
                            is_optional=True,
                        ),
                        'Configurations': Field(
                            List(Field(PermissiveDict())),
                            description='''A list of additional configurations to apply within a
                                configuration object.''',
                            is_optional=True,
                        ),
                        'Properties': Field(
                            PermissiveDict(),
                            description='''A set of properties specified within a configuration
                                classification.''',
                            is_optional=True,
                        ),
                    }
                ),
                description='''An optional configuration specification to be used when provisioning
                    cluster instances, which can include configurations for applications and 
                    software bundled with Amazon EMR. A configuration consists of a classification,
                    properties, and optional nested configurations. A classification refers to an
                    application-specific configuration file. Properties are the settings you want to
                    change in that file. For more information, see the EMR Configuring Applications
                    guide.''',
                is_optional=True,
            )
        ),
        description='''For Amazon EMR releases 4.0 and later. The list of configurations supplied
            for the EMR cluster you are creating.''',
        is_optional=True,
    )


def _define_emr_step_type():
    name = Field(String, description='The name of the step.', is_optional=False)

    actionOnFailure = Field(
        EmrActionOnFailure,
        description='''The action to take when the cluster step fails. Possible values are
        TERMINATE_CLUSTER, CANCEL_AND_WAIT, and CONTINUE. TERMINATE_JOB_FLOW is provided for
        backward compatibility. We recommend using TERMINATE_CLUSTER instead.''',
        is_optional=True,
    )

    hadoopJarStep = Field(
        Dict(
            fields={
                'Properties': Field(
                    List(
                        Field(
                            Dict(fields={'Key': Field(String), 'Value': Field(String)}),
                            description='A key value pair.',
                        )
                    ),
                    description='''A list of Java properties that are set when the step runs. You
                    can use these properties to pass key value pairs to your main function.''',
                    is_optional=True,
                ),
                'Jar': Field(
                    String,
                    description='A path to a JAR file run during the step.',
                    is_optional=False,
                ),
                'MainClass': Field(
                    String,
                    description='''The name of the main class in the specified Java file. If not
                    specified, the JAR file should specify a Main-Class in its manifest file.''',
                    is_optional=True,
                ),
                'Args': Field(
                    List(String),
                    description='''A list of command line arguments passed to the JAR file's main
                    function when executed.''',
                    is_optional=True,
                ),
            }
        ),
        description='The JAR file used for the step.',
    )

    return Field(
        Dict(
            fields={
                'Name': name,
                'ActionOnFailure': actionOnFailure,
                'HadoopJarStep': hadoopJarStep,
            }
        ),
        description='Specification of a cluster (job flow) step.',
        is_optional=True,
    )


def _define_bootstrap_action_type():
    name = Field(String, description='The name of the bootstrap action.', is_optional=False)

    path = Field(
        String,
        description='''Location of the script to run during a bootstrap action. Can be either a
        location in Amazon S3 or on a local file system.''',
        is_optional=False,
    )

    args = Field(
        List(String),
        description='A list of command line arguments to pass to the bootstrap action script.',
        is_optional=True,
    )

    return Field(
        Dict(
            fields={
                'Name': name,
                'ScriptBootstrapAction': Field(
                    Dict(fields={'Path': path, 'Args': args}),
                    description='The script run by the bootstrap action.',
                    is_optional=False,
                ),
            }
        ),
        description='Configuration of a bootstrap action.',
        is_optional=True,
    )


def _define_ebs_configuration():
    return Field(
        Dict(
            fields={
                'EbsBlockDeviceConfigs': Field(
                    List(
                        Field(
                            Dict(
                                fields={
                                    'VolumeSpecification': Field(
                                        Dict(
                                            fields={
                                                'VolumeType': Field(
                                                    String,
                                                    description='The volume type. Volume types supported are gp2, io1, standard.',
                                                    is_optional=False,
                                                ),
                                                'Iops': Field(
                                                    Int,
                                                    description='The number of I/O operations per second (IOPS) that the volume supports.',
                                                    is_optional=True,
                                                ),
                                                'SizeInGB': Field(
                                                    Int,
                                                    'The volume size, in gibibytes (GiB). This can be a number from 1 - 1024. If the volume type is EBS-optimized, the minimum value is 10.',
                                                    is_optional=False,
                                                ),
                                            }
                                        ),
                                        description='''EBS volume specifications such as volume type, IOPS, and size (GiB) that will be requested for the EBS volume attached to an EC2 instance in the cluster.''',
                                        is_optional=False,
                                    ),
                                    'VolumesPerInstance': Field(
                                        Int,
                                        description='Number of EBS volumes with a specific volume configuration that will be associated with every instance in the instance group',
                                        is_optional=True,
                                    ),
                                }
                            ),
                            description='''Configuration of requested EBS block device associated
                            with the instance group with count of volumes that will be associated
                            to every instance.''',
                            is_optional=True,
                        )
                    ),
                    description='''An array of Amazon EBS volume specifications attached to a
                    cluster instance.''',
                    is_optional=True,
                ),
                'EbsOptimized': Field(
                    Bool,
                    description='Indicates whether an Amazon EBS volume is EBS-optimized.',
                    is_optional=True,
                ),
            }
        ),
        description='''EBS configurations that will be attached to each EC2 instance in the
        instance group.''',
        is_optional=True,
    )


def define_emr_run_job_flow_config():
    name = Field(String, description='The name of the job flow.', is_optional=False)

    log_uri = Field(
        String,
        description='''The location in Amazon S3 to write the log files of the job flow. If a value
        is not provided, logs are not created.''',
        is_optional=True,
    )

    additional_info = Field(
        String, description='A JSON string for selecting additional features.', is_optional=True
    )

    ami_version = Field(
        String,
        description='''Applies only to Amazon EMR AMI versions 3.x and 2.x. For Amazon EMR releases
        4.0 and later, ReleaseLabel is used. To specify a custom AMI, use CustomAmiID.''',
        is_optional=True,
    )

    release_label = Field(
        String,
        description='''The Amazon EMR release label, which determines the version of open-source
        application packages installed on the cluster. Release labels are in the form emr-x.x.x,
        where x.x.x is an Amazon EMR release version, for example, emr-5.14.0 . For more information
        about Amazon EMR release versions and included application versions and features, see
        https://docs.aws.amazon.com/emr/latest/ReleaseGuide/. The release label applies only to
        Amazon EMR releases versions 4.x and later. Earlier versions use AmiVersion.''',
        is_optional=True,
    )

    instance_groups = Field(
        List(
            Field(
                Dict(
                    fields={
                        'Name': Field(
                            String,
                            description='Friendly name given to the instance group.',
                            is_optional=True,
                        ),
                        'Market': Field(
                            EmrMarket,
                            description='''Market type of the EC2 instances used to create a cluster
                            node.''',
                            is_optional=True,
                        ),
                        'InstanceRole': Field(
                            EmrInstanceRole,
                            description='The role of the instance group in the cluster.',
                            is_optional=False,
                        ),
                        'BidPrice': Field(
                            String,
                            description='''The maximum Spot price your are willing to pay for EC2
                            instances.

                            An optional, nullable field that applies if the MarketType for the
                            instance group is specified as SPOT . Specify the maximum spot price in
                            USD. If the value is NULL and SPOT is specified, the maximum Spot price
                            is set equal to the On-Demand price.''',
                            is_optional=True,
                        ),
                        'InstanceType': Field(
                            String,
                            description='''The EC2 instance type for all instances in the instance
                            group.''',
                            is_optional=False,
                        ),
                        'InstanceCount': Field(
                            Int,
                            description='Target number of instances for the instance group.',
                            is_optional=False,
                        ),
                        'Configurations': _define_configurations(),
                        'EbsConfiguration': _define_ebs_configuration(),
                        # 'AutoScalingPolicy': {
                        #     'Constraints': {
                        #         'MinCapacity': 123,
                        #         'MaxCapacity': 123
                        #     },
                        #     'Rules': [
                        #         {
                        #             'Name': 'string',
                        #             'Description': 'string',
                        #             'Action': {
                        #                 'Market': 'ON_DEMAND'|'SPOT',
                        #                 'SimpleScalingPolicyConfiguration': {
                        #                     'AdjustmentType': 'CHANGE_IN_CAPACITY'|'PERCENT_CHANGE_IN_CAPACITY'|'EXACT_CAPACITY',
                        #                     'ScalingAdjustment': 123,
                        #                     'CoolDown': 123
                        #                 }
                        #             },
                        #             'Trigger': {
                        #                 'CloudWatchAlarmDefinition': {
                        #                     'ComparisonOperator': 'GREATER_THAN_OR_EQUAL'|'GREATER_THAN'|'LESS_THAN'|'LESS_THAN_OR_EQUAL',
                        #                     'EvaluationPeriods': 123,
                        #                     'MetricName': 'string',
                        #                     'Namespace': 'string',
                        #                     'Period': 123,
                        #                     'Statistic': 'SAMPLE_COUNT'|'AVERAGE'|'SUM'|'MINIMUM'|'MAXIMUM',
                        #                     'Threshold': 123.0,
                        #                     'Unit': 'NONE'|'SECONDS'|'MICRO_SECONDS'|'MILLI_SECONDS'|'BYTES'|'KILO_BYTES'|'MEGA_BYTES'|'GIGA_BYTES'|'TERA_BYTES'|'BITS'|'KILO_BITS'|'MEGA_BITS'|'GIGA_BITS'|'TERA_BITS'|'PERCENT'|'COUNT'|'BYTES_PER_SECOND'|'KILO_BYTES_PER_SECOND'|'MEGA_BYTES_PER_SECOND'|'GIGA_BYTES_PER_SECOND'|'TERA_BYTES_PER_SECOND'|'BITS_PER_SECOND'|'KILO_BITS_PER_SECOND'|'MEGA_BITS_PER_SECOND'|'GIGA_BITS_PER_SECOND'|'TERA_BITS_PER_SECOND'|'COUNT_PER_SECOND',
                        #                     'Dimensions': [
                        #                         {
                        #                             'Key': 'string',
                        #                             'Value': 'string'
                        #                         },
                        #                     ]
                        #                 }
                        #             }
                        #         },
                        #     ]
                        # }
                    }
                ),
                description='Configuration defining a new instance group.',
                is_optional=True,
            )
        ),
        description='Configuration for the instance groups in a cluster.',
        is_optional=True,
    )

    #     'InstanceFleets': [
    #         {
    #             'Name': 'string',
    #             'InstanceFleetType': 'MASTER'|'CORE'|'TASK',
    #             'TargetOnDemandCapacity': 123,
    #             'TargetSpotCapacity': 123,
    #             'InstanceTypeConfigs': [
    #                 {
    #                     'InstanceType': 'string',
    #                     'WeightedCapacity': 123,
    #                     'BidPrice': 'string',
    #                     'BidPriceAsPercentageOfOnDemandPrice': 123.0,
    #                     'EbsConfiguration': {
    #                         'EbsBlockDeviceConfigs': [
    #                             {
    #                                 'VolumeSpecification': {
    #                                     'VolumeType': 'string',
    #                                     'Iops': 123,
    #                                     'SizeInGB': 123
    #                                 },
    #                                 'VolumesPerInstance': 123
    #                             },
    #                         ],
    #                         'EbsOptimized': True|False
    #                     },
    #                     'Configurations': [
    #                         {
    #                             'Classification': 'string',
    #                             'Configurations': {'... recursive ...'},
    #                             'Properties': {
    #                                 'string': 'string'
    #                             }
    #                         },
    #                     ]
    #                 },
    #             ],
    #             'LaunchSpecifications': {
    #                 'SpotSpecification': {
    #                     'TimeoutDurationMinutes': 123,
    #                     'TimeoutAction': 'SWITCH_TO_ON_DEMAND'|'TERMINATE_CLUSTER',
    #                     'BlockDurationMinutes': 123
    #                 }
    #             }
    #         },
    #     ],
    instance_fleets = Field(Dict(fields={}))

    instances = Field(
        Dict(
            fields={
                'MasterInstanceType': Field(
                    String,
                    description='The EC2 instance type of the master node.',
                    is_optional=True,
                ),
                'SlaveInstanceType': Field(
                    String,
                    description='The EC2 instance type of the core and task nodes.',
                    is_optional=True,
                ),
                'InstanceCount': Field(
                    Int, description='The number of EC2 instances in the cluster.', is_optional=True
                ),
                'InstanceGroups': instance_groups,
                'InstanceFleets': instance_fleets,
                'Ec2KeyName': Field(
                    String,
                    description='''The name of the EC2 key pair that can be used to ssh to the
                    master node as the user called "hadoop."''',
                    is_optional=True,
                ),
                'Placement': Field(
                    Dict(
                        fields={
                            'AvailabilityZone': Field(
                                String,
                                description='''The Amazon EC2 Availability Zone for the cluster.
                                AvailabilityZone is used for uniform instance groups, while
                                AvailabilityZones (plural) is used for instance fleets.''',
                                is_optional=True,
                            ),
                            'AvailabilityZones': Field(
                                List(Field(String)),
                                description='''When multiple Availability Zones are specified,
                                Amazon EMR evaluates them and launches instances in the optimal
                                Availability Zone. AvailabilityZones is used for instance fleets,
                                while AvailabilityZone (singular) is used for uniform instance
                                groups.''',
                                is_optional=True,
                            ),
                        }
                    ),
                    description='The Availability Zone in which the cluster runs.',
                    is_optional=True,
                ),
                'KeepJobFlowAliveWhenNoSteps': Field(
                    Bool,
                    description='''Specifies whether the cluster should remain available after
                    completing all steps.''',
                    is_optional=True,
                ),
                'TerminationProtected': Field(
                    Bool,
                    description='''Specifies whether to lock the cluster to prevent the Amazon EC2
                    instances from being terminated by API call, user intervention, or in the event
                    of a job-flow error.''',
                    is_optional=True,
                ),
                'HadoopVersion': Field(
                    String,
                    description='''Applies only to Amazon EMR release versions earlier than 4.0. The
                    Hadoop version for the cluster. Valid inputs are "0.18" (deprecated), "0.20"
                    (deprecated), "0.20.205" (deprecated), "1.0.3", "2.2.0", or "2.4.0". If you do
                    not set this value, the default of 0.18 is used, unless the AmiVersion parameter
                    is set in the RunJobFlow call, in which case the default version of Hadoop for
                    that AMI version is used.''',
                    is_optional=True,
                ),
                'Ec2SubnetId': Field(
                    String,
                    description='''Applies to clusters that use the uniform instance group
                    configuration. To launch the cluster in Amazon Virtual Private Cloud (Amazon
                    VPC), set this parameter to the identifier of the Amazon VPC subnet where you
                    want the cluster to launch. If you do not specify this value, the cluster
                    launches in the normal Amazon Web Services cloud, outside of an Amazon VPC, if
                    the account launching the cluster supports EC2 Classic networks in the region
                    where the cluster launches.

                    Amazon VPC currently does not support cluster compute quadruple extra large
                    (cc1.4xlarge) instances. Thus you cannot specify the cc1.4xlarge instance type
                    for clusters launched in an Amazon VPC.''',
                    is_optional=True,
                ),
                'Ec2SubnetIds': Field(
                    List(Field(String)),
                    description='''Applies to clusters that use the instance fleet configuration.
                    When multiple EC2 subnet IDs are specified, Amazon EMR evaluates them and
                    launches instances in the optimal subnet.''',
                    is_optional=True,
                ),
                'EmrManagedMasterSecurityGroup': Field(
                    String,
                    description='''The identifier of the Amazon EC2 security group for the master
                    node.''',
                    is_optional=True,
                ),
                'EmrManagedSlaveSecurityGroup': Field(
                    String,
                    description='''The identifier of the Amazon EC2 security group for the core and
                    task nodes.''',
                    is_optional=True,
                ),
                'ServiceAccessSecurityGroup': Field(
                    String,
                    description='''The identifier of the Amazon EC2 security group for the Amazon
                    EMR service to access clusters in VPC private subnets.''',
                    is_optional=True,
                ),
                'AdditionalMasterSecurityGroups': Field(
                    List(Field(String)),
                    description='''A list of additional Amazon EC2 security group IDs for the master
                    node.''',
                    is_optional=True,
                ),
                'AdditionalSlaveSecurityGroups': Field(
                    List(Field(String)),
                    description='''A list of additional Amazon EC2 security group IDs for the core
                    and task nodes.''',
                    is_optional=True,
                ),
            }
        ),
        description='A specification of the number and type of Amazon EC2 instances.',
        is_optional=False,
    )

    steps = Field(List(_define_emr_step_type()), description='A list of steps to run.')

    bootstrap_actions = Field(
        List(_define_bootstrap_action_type()),
        description='''A list of bootstrap actions to run before Hadoop starts on the
                    cluster nodes.''',
        is_optional=True,
    )

    supported_products = Field(
        List(Field(EmrSupportedProducts)),
        description='''A list of strings that indicates third-party software to use. For
                    more information, see the Amazon EMR Developer Guide. Currently supported
                    values are:
                        - "mapr-m3" - launch the job flow using MapR M3 Edition.
                        - "mapr-m5" - launch the job flow using MapR M5 Edition.
                    ''',
        is_optional=True,
    )

    new_supported_products = Field(
        List(
            Field(
                Dict(
                    fields={
                        'Name': Field(String, is_optional=False),
                        'Args': Field(
                            List(String), description='The list of user-supplied arguments.'
                        ),
                    }
                ),
                description='''The list of supported product configurations which allow user-
                supplied arguments. EMR accepts these arguments and forwards them to the 
                corresponding installation script as bootstrap action arguments.''',
            )
        ),
        description='''A list of strings that indicates third-party software to use with the job
        flow that accepts a user argument list. EMR accepts and forwards the argument list to the
        corresponding installation script as bootstrap action arguments. For more information, see
        "Launch a Job Flow on the MapR Distribution for Hadoop" in the Amazon EMR Developer Guide.
        
        Supported values are:

        - "mapr-m3" - launch the cluster using MapR M3 Edition.
        - "mapr-m5" - launch the cluster using MapR M5 Edition.
        - "mapr" with the user arguments specifying "--edition,m3" or "--edition,m5" - launch the 
            job flow using MapR M3 or M5 Edition respectively.
        - "mapr-m7" - launch the cluster using MapR M7 Edition.
        - "hunk" - launch the cluster with the Hunk Big Data Analtics Platform.
        - "hue"- launch the cluster with Hue installed.
        - "spark" - launch the cluster with Apache Spark installed.
        - "ganglia" - launch the cluster with the Ganglia Monitoring System installed.''',
        is_optional=True,
    )

    applications = Field(
        List(
            Field(
                Dict(
                    fields={
                        'Name': Field(
                            String, description='The name of the application.', is_optional=False
                        ),
                        'Version': Field(
                            String, description='The version of the application.', is_optional=True
                        ),
                        'Args': Field(
                            List(Field(String)),
                            description='Arguments for Amazon EMR to pass to the application.',
                            is_optional=True,
                        ),
                        'AdditionalInfo': Field(
                            PermissiveDict(),
                            description='''This option is for advanced users only. This is meta
                            information about third-party applications that third-party vendors use
                            for testing purposes.''',
                            is_optional=True,
                        ),
                    }
                ),
                description='''With Amazon EMR release version 4.0 and later, the only accepted
                parameter is the application name. To pass arguments to applications, you use 
                configuration classifications specified using configuration JSON objects. For more
                information, see the EMR Configuring Applications guide.

                With earlier Amazon EMR releases, the application is any Amazon or third-party
                software that you can add to the cluster. This structure contains a list of strings
                that indicates the software to use with the cluster and accepts a user argument
                list. Amazon EMR accepts and forwards the argument list to the corresponding
                installation script as bootstrap action argument.
                ''',
                is_optional=True,
            )
        ),
        description='''Applies to Amazon EMR releases 4.0 and later. A case-insensitive list of
        applications for Amazon EMR to install and configure when launching the cluster. For a list
        of applications available for each Amazon EMR release version, see the Amazon EMR Release
        Guide.''',
        is_optional=True,
    )

    visible_to_all_users = Field(
        Bool,
        description='''Whether the cluster is visible to all IAM users of the AWS account associated
        with the cluster. If this value is set to True, all IAM users of that AWS account can view
        and (if they have the proper policy permissions set) manage the cluster. If it is set to 
        False, only the IAM user that created the cluster can view and manage it.''',
        is_optional=True,
    )

    job_flow_role = Field(
        String,
        description='''Also called instance profile and EC2 role. An IAM role for an EMR cluster.
        The EC2 instances of the cluster assume this role. The default role is EMR_EC2_DefaultRole.
        In order to use the default role, you must have already created it using the CLI or console.
        ''',
        is_optional=True,
    )

    service_role = Field(
        String,
        description='''The IAM role that will be assumed by the Amazon EMR service to access AWS
        resources on your behalf.''',
        is_optional=True,
    )

    tags = Field(
        List(
            Field(
                Dict(
                    fields={
                        'Key': Field(
                            String,
                            description='''A user-defined key, which is the minimum required
                            information for a valid tag. For more information, see the EMR Tag
                            guide.''',
                            is_optional=False,
                        ),
                        'Value': Field(
                            String,
                            description='''A user-defined value, which is optional in a tag. For
                            more information, see the EMR Tag Clusters guide.''',
                            is_optional=True,
                        ),
                    }
                ),
                description='''A key/value pair containing user-defined metadata that you can
                associate with an Amazon EMR resource. Tags make it easier to associate clusters in
                various ways, such as grouping clusters to track your Amazon EMR resource allocation
                costs. For more information, see the EMR Tag Clusters guide.''',
            )
        ),
        description='''A list of tags to associate with a cluster and propagate to Amazon EC2
        instances.''',
        is_optional=True,
    )

    security_configuration = Field(
        String,
        description='The name of a security configuration to apply to the cluster.',
        is_optional=True,
    )

    auto_scaling_role = Field(
        String,
        description='''An IAM role for automatic scaling policies. The default role is
        EMR_AutoScaling_DefaultRole. The IAM role provides permissions that the automatic scaling
        feature requires to launch and terminate EC2 instances in an instance group.''',
        is_optional=True,
    )

    scale_down_behavior = Field(
        EmrScaleDownBehavior,
        description='''Specifies the way that individual Amazon EC2 instances terminate when an
        automatic scale-in activity occurs or an instance group is resized.
        TERMINATE_AT_INSTANCE_HOUR indicates that Amazon EMR terminates nodes at the instance-hour
        boundary, regardless of when the request to terminate the instance was submitted. This
        option is only available with Amazon EMR 5.1.0 and later and is the default for clusters
        created using that version. TERMINATE_AT_TASK_COMPLETION indicates that Amazon EMR
        blacklists and drains tasks from nodes before terminating the Amazon EC2 instances,
        regardless of the instance-hour boundary. With either behavior, Amazon EMR removes the least
        active nodes first and blocks instance termination if it could lead to HDFS corruption.
        TERMINATE_AT_TASK_COMPLETION available only in Amazon EMR version 4.1.0 and later, and is
        the default for versions of Amazon EMR earlier than 5.1.0.''',
        is_optional=True,
    )

    custom_ami_id = Field(
        String,
        description='''Available only in Amazon EMR version 5.7.0 and later. The ID of a custom
        Amazon EBS-backed Linux AMI. If specified, Amazon EMR uses this AMI when it launches cluster
        EC2 instances. For more information about custom AMIs in Amazon EMR, see Using a Custom AMI
        in the Amazon EMR Management Guide. If omitted, the cluster uses the base Linux AMI for the
        ReleaseLabel specified. For Amazon EMR versions 2.x and 3.x, use AmiVersion instead.

        For information about creating a custom AMI, see Creating an Amazon EBS-Backed Linux AMI in
        the Amazon Elastic Compute Cloud User Guide for Linux Instances. For information about
        finding an AMI ID, see Finding a Linux AMI.''',
        is_optional=True,
    )

    repo_upgrade_on_boot = Field(
        EmrRepoUpgradeOnBoot,
        description='''Applies only when CustomAmiID is used. Specifies which updates from the
        Amazon Linux AMI package repositories to apply automatically when the instance boots using
        the AMI. If omitted, the default is SECURITY , which indicates that only security updates
        are applied. If NONE is specified, no updates are applied, and all updates must be applied
        manually.''',
        is_optional=True,
    )

    kerberos_attributes = Field(
        Dict(
            fields={
                'Realm': Field(
                    String,
                    description='''The name of the Kerberos realm to which all nodes in a cluster
                    belong. For example, EC2.INTERNAL.''',
                    is_optional=False,
                ),
                'KdcAdminPassword': Field(
                    String,
                    description='''The password used within the cluster for the kadmin service on
                    the cluster-dedicated KDC, which maintains Kerberos principals, password
                    policies, and keytabs for the cluster.''',
                    is_optional=False,
                ),
                'CrossRealmTrustPrincipalPassword': Field(
                    String,
                    description='''Required only when establishing a cross-realm trust with a KDC in
                    a different realm. The cross-realm principal password, which must be identical
                    across realms.''',
                    is_optional=True,
                ),
                'ADDomainJoinUser': Field(
                    String,
                    description='''Required only when establishing a cross-realm trust with an
                    Active Directory domain. A user with sufficient privileges to join resources to
                    the domain.''',
                    is_optional=True,
                ),
                'ADDomainJoinPassword': Field(
                    String,
                    description='''The Active Directory password for ADDomainJoinUser.''',
                    is_optional=True,
                ),
            }
        ),
        description='''Attributes for Kerberos configuration when Kerberos authentication is enabled
        using a security configuration. For more information see Use Kerberos Authentication in the
        EMR Management Guide .''',
        is_optional=True,
    )

    return Field(
        Dict(
            fields={
                'Name': name,
                'LogUri': log_uri,
                'AdditionalInfo': additional_info,
                'AmiVersion': ami_version,
                'ReleaseLabel': release_label,
                'Instances': instances,
                'Steps': steps,
                'BootstrapActions': bootstrap_actions,
                'SupportedProducts': supported_products,
                'NewSupportedProducts': new_supported_products,
                'Applications': applications,
                'Configurations': _define_configurations(),
                'VisibleToAllUsers': visible_to_all_users,
                'JobFlowRole': job_flow_role,
                'ServiceRole': service_role,
                'Tags': tags,
                'SecurityConfiguration': security_configuration,
                'AutoScalingRole': auto_scaling_role,
                'ScaleDownBehavior': scale_down_behavior,
                'CustomAmiId': custom_ami_id,
                'EbsRootVolumeSize': Field(
                    Int,
                    description='''The size, in GiB, of the EBS root device volume of the Linux AMI
                    that is used for each EC2 instance. Available in Amazon EMR version 4.x and
                    later.''',
                    is_optional=True,
                ),
                'RepoUpgradeOnBoot': repo_upgrade_on_boot,
                'KerberosAttributes': kerberos_attributes,
            }
        ),
        description='AWS EMR run job flow configuration',
    )
