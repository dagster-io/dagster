from dagster import Bool, Dict, Field, List, PermissiveDict, String

from .types import EmrActionOnFailure, EmrSupportedProducts

#     Instances={
#         'MasterInstanceType': 'string',
#         'SlaveInstanceType': 'string',
#         'InstanceCount': 123,
#         'InstanceGroups': [
#             {
#                 'Name': 'string',
#                 'Market': 'ON_DEMAND'|'SPOT',
#                 'InstanceRole': 'MASTER'|'CORE'|'TASK',
#                 'BidPrice': 'string',
#                 'InstanceType': 'string',
#                 'InstanceCount': 123,
#                 'Configurations': [
#                     {
#                         'Classification': 'string',
#                         'Configurations': {'... recursive ...'},
#                         'Properties': {
#                             'string': 'string'
#                         }
#                     },
#                 ],
#                 'EbsConfiguration': {
#                     'EbsBlockDeviceConfigs': [
#                         {
#                             'VolumeSpecification': {
#                                 'VolumeType': 'string',
#                                 'Iops': 123,
#                                 'SizeInGB': 123
#                             },
#                             'VolumesPerInstance': 123
#                         },
#                     ],
#                     'EbsOptimized': True|False
#                 },
#                 'AutoScalingPolicy': {
#                     'Constraints': {
#                         'MinCapacity': 123,
#                         'MaxCapacity': 123
#                     },
#                     'Rules': [
#                         {
#                             'Name': 'string',
#                             'Description': 'string',
#                             'Action': {
#                                 'Market': 'ON_DEMAND'|'SPOT',
#                                 'SimpleScalingPolicyConfiguration': {
#                                     'AdjustmentType': 'CHANGE_IN_CAPACITY'|'PERCENT_CHANGE_IN_CAPACITY'|'EXACT_CAPACITY',
#                                     'ScalingAdjustment': 123,
#                                     'CoolDown': 123
#                                 }
#                             },
#                             'Trigger': {
#                                 'CloudWatchAlarmDefinition': {
#                                     'ComparisonOperator': 'GREATER_THAN_OR_EQUAL'|'GREATER_THAN'|'LESS_THAN'|'LESS_THAN_OR_EQUAL',
#                                     'EvaluationPeriods': 123,
#                                     'MetricName': 'string',
#                                     'Namespace': 'string',
#                                     'Period': 123,
#                                     'Statistic': 'SAMPLE_COUNT'|'AVERAGE'|'SUM'|'MINIMUM'|'MAXIMUM',
#                                     'Threshold': 123.0,
#                                     'Unit': 'NONE'|'SECONDS'|'MICRO_SECONDS'|'MILLI_SECONDS'|'BYTES'|'KILO_BYTES'|'MEGA_BYTES'|'GIGA_BYTES'|'TERA_BYTES'|'BITS'|'KILO_BITS'|'MEGA_BITS'|'GIGA_BITS'|'TERA_BITS'|'PERCENT'|'COUNT'|'BYTES_PER_SECOND'|'KILO_BYTES_PER_SECOND'|'MEGA_BYTES_PER_SECOND'|'GIGA_BYTES_PER_SECOND'|'TERA_BYTES_PER_SECOND'|'BITS_PER_SECOND'|'KILO_BITS_PER_SECOND'|'MEGA_BITS_PER_SECOND'|'GIGA_BITS_PER_SECOND'|'TERA_BITS_PER_SECOND'|'COUNT_PER_SECOND',
#                                     'Dimensions': [
#                                         {
#                                             'Key': 'string',
#                                             'Value': 'string'
#                                         },
#                                     ]
#                                 }
#                             }
#                         },
#                     ]
#                 }
#             },
#         ],
#         'InstanceFleets': [
#             {
#                 'Name': 'string',
#                 'InstanceFleetType': 'MASTER'|'CORE'|'TASK',
#                 'TargetOnDemandCapacity': 123,
#                 'TargetSpotCapacity': 123,
#                 'InstanceTypeConfigs': [
#                     {
#                         'InstanceType': 'string',
#                         'WeightedCapacity': 123,
#                         'BidPrice': 'string',
#                         'BidPriceAsPercentageOfOnDemandPrice': 123.0,
#                         'EbsConfiguration': {
#                             'EbsBlockDeviceConfigs': [
#                                 {
#                                     'VolumeSpecification': {
#                                         'VolumeType': 'string',
#                                         'Iops': 123,
#                                         'SizeInGB': 123
#                                     },
#                                     'VolumesPerInstance': 123
#                                 },
#                             ],
#                             'EbsOptimized': True|False
#                         },
#                         'Configurations': [
#                             {
#                                 'Classification': 'string',
#                                 'Configurations': {'... recursive ...'},
#                                 'Properties': {
#                                     'string': 'string'
#                                 }
#                             },
#                         ]
#                     },
#                 ],
#                 'LaunchSpecifications': {
#                     'SpotSpecification': {
#                         'TimeoutDurationMinutes': 123,
#                         'TimeoutAction': 'SWITCH_TO_ON_DEMAND'|'TERMINATE_CLUSTER',
#                         'BlockDurationMinutes': 123
#                     }
#                 }
#             },
#         ],
#         'Ec2KeyName': 'string',
#         'Placement': {
#             'AvailabilityZone': 'string',
#             'AvailabilityZones': [
#                 'string',
#             ]
#         },
#         'KeepJobFlowAliveWhenNoSteps': True|False,
#         'TerminationProtected': True|False,
#         'HadoopVersion': 'string',
#         'Ec2SubnetId': 'string',
#         'Ec2SubnetIds': [
#             'string',
#         ],
#         'EmrManagedMasterSecurityGroup': 'string',
#         'EmrManagedSlaveSecurityGroup': 'string',
#         'ServiceAccessSecurityGroup': 'string',
#         'AdditionalMasterSecurityGroups': [
#             'string',
#         ],
#         'AdditionalSlaveSecurityGroups': [
#             'string',
#         ]
#     },


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

    configurations = Field(
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
                cluster instances, which can include configurations for applications and software
                bundled with Amazon EMR. A configuration consists of a classification, properties,
                and optional nested configurations. A classification refers to an application-
                specific configuration file. Properties are the settings you want to change in that
                file. For more information, see the EMR Configuring Applications guide.''',
                is_optional=True,
            )
        ),
        description='''For Amazon EMR releases 4.0 and later. The list of configurations supplied
        for the EMR cluster you are creating.''',
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

    #     ScaleDownBehavior='TERMINATE_AT_INSTANCE_HOUR'|'TERMINATE_AT_TASK_COMPLETION',
    #     CustomAmiId='string',
    #     EbsRootVolumeSize=123,
    #     RepoUpgradeOnBoot='SECURITY'|'NONE',
    #     KerberosAttributes={
    #         'Realm': 'string',
    #         'KdcAdminPassword': 'string',
    #         'CrossRealmTrustPrincipalPassword': 'string',
    #         'ADDomainJoinUser': 'string',
    #         'ADDomainJoinPassword': 'string'
    #     }
    # )

    return Field(
        Dict(
            fields={
                'Name': name,
                'LogUri': log_uri,
                'AdditionalInfo': additional_info,
                'AmiVersion': ami_version,
                'ReleaseLabel': release_label,
                # TODO: Instances
                'Steps': steps,
                'BootstrapActions': bootstrap_actions,
                'SupportedProducts': supported_products,
                'NewSupportedProducts': new_supported_products,
                'Applications': applications,
                'Configurations': configurations,
                'VisibleToAllUsers': visible_to_all_users,
                'JobFlowRole': job_flow_role,
                'ServiceRole': service_role,
                'Tags': tags,
                'SecurityConfiguration': Field(
                    String,
                    description='The name of a security configuration to apply to the cluster.',
                    is_optional=True,
                ),
                'AutoScalingRole': Field(
                    String,
                    description='''An IAM role for automatic scaling policies. The default role is
                    EMR_AutoScaling_DefaultRole . The IAM role provides permissions that the
                    automatic scaling feature requires to launch and terminate EC2 instances in an
                    instance group.''',
                    is_optional=True,
                ),
            }
        ),
        description='AWS EMR run job flow configuration',
    )
