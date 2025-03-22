"""NOTE: THIS FILE IS AUTO-GENERATED. DO NOT EDIT.

@generated

Produced via:
parse_dataproc_configs.py \

"""

from dagster import Enum, EnumValue

PrivateIpv6GoogleAccess = Enum(
    name="PrivateIpv6GoogleAccess",
    enum_values=[
        EnumValue(
            "PRIVATE_IPV6_GOOGLE_ACCESS_UNSPECIFIED",
            description="""If unspecified, Compute
        Engine default behavior will apply, which is the same as INHERIT_FROM_SUBNETWORK.""",
        ),
        EnumValue(
            "INHERIT_FROM_SUBNETWORK",
            description="""Private access to and from Google
        Services configuration inherited from the subnetwork configuration. This is the default
        Compute Engine behavior.""",
        ),
        EnumValue(
            "OUTBOUND",
            description="""Enables outbound private IPv6 access to Google Services
        from the Dataproc cluster.""",
        ),
        EnumValue(
            "BIDIRECTIONAL",
            description="""Enables bidirectional private IPv6 access between
        Google Services and the Dataproc cluster.""",
        ),
    ],
)

ConsumeReservationType = Enum(
    name="ConsumeReservationType",
    enum_values=[
        EnumValue("TYPE_UNSPECIFIED", description=""""""),
        EnumValue("NO_RESERVATION", description="""Do not consume from any allocated capacity."""),
        EnumValue("ANY_RESERVATION", description="""Consume any reservation available."""),
        EnumValue(
            "SPECIFIC_RESERVATION",
            description="""Must consume from a specific reservation.
        Must specify key value fields for specifying the reservations.""",
        ),
    ],
)

Preemptibility = Enum(
    name="Preemptibility",
    enum_values=[
        EnumValue(
            "PREEMPTIBILITY_UNSPECIFIED",
            description="""Preemptibility is unspecified, the
        system will choose the appropriate setting for each instance group.""",
        ),
        EnumValue(
            "NON_PREEMPTIBLE",
            description="""Instances are non-preemptible.This option is
        allowed for all instance groups and is the only valid value for Master and Worker instance
        groups.""",
        ),
        EnumValue(
            "PREEMPTIBLE",
            description="""Instances are preemptible
        (https://cloud.google.com/compute/docs/instances/preemptible).This option is allowed only
        for secondary worker (https://cloud.google.com/dataproc/docs/concepts/compute/secondary-vms)
        groups.""",
        ),
        EnumValue(
            "SPOT",
            description="""Instances are Spot VMs
        (https://cloud.google.com/compute/docs/instances/spot).This option is allowed only for
        secondary worker (https://cloud.google.com/dataproc/docs/concepts/compute/secondary-vms)
        groups. Spot VMs are the latest version of preemptible VMs
        (https://cloud.google.com/compute/docs/instances/preemptible), and provide additional
        features.""",
        ),
    ],
)

Component = Enum(
    name="Component",
    enum_values=[
        EnumValue("ROLE_UNSPECIFIED", description="""Required unspecified role."""),
        EnumValue("DRIVER", description="""Job drivers run on the node pool."""),
    ],
)

MetricSource = Enum(
    name="MetricSource",
    enum_values=[
        EnumValue(
            "METRIC_SOURCE_UNSPECIFIED",
            description="""Required unspecified metric
        source.""",
        ),
        EnumValue(
            "MONITORING_AGENT_DEFAULTS",
            description="""Monitoring agent metrics. If this
        source is enabled, Dataproc enables the monitoring agent in Compute Engine, and collects
        monitoring agent metrics, which are published with an agent.googleapis.com prefix.""",
        ),
        EnumValue("HDFS", description="""HDFS metric source."""),
        EnumValue("SPARK", description="""Spark metric source."""),
        EnumValue("YARN", description="""YARN metric source."""),
        EnumValue("SPARK_HISTORY_SERVER", description="""Spark History Server metric source."""),
        EnumValue("HIVESERVER2", description="""Hiveserver2 metric source."""),
        EnumValue("HIVEMETASTORE", description="""hivemetastore metric source"""),
        EnumValue("FLINK", description="""flink metric source"""),
    ],
)
