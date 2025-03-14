"""NOTE: THIS FILE IS AUTO-GENERATED. DO NOT EDIT.

@generated

Produced via:
parse_dataproc_configs.py \

"""

from dagster import Bool, Field, Int, Permissive, Shape, String

from dagster_gcp.dataproc.types_dataproc_cluster import (
    Component,
    ConsumeReservationType,
    MetricSource,
    Preemptibility,
    PrivateIpv6GoogleAccess,
)


def define_dataproc_cluster_config():
    return Field(
        Shape(
            fields={
                "configBucket": Field(
                    String,
                    description="""Optional. A Cloud Storage bucket used to stage job dependencies,
                    config files, and job driver console output. If you do not specify a staging
                    bucket, Cloud Dataproc will determine a Cloud Storage location (US, ASIA, or EU)
                    for your cluster\'s staging bucket according to the Compute Engine zone where
                    your cluster is deployed, and then create and manage this project-level,
                    per-location bucket (see Dataproc staging and temp buckets
                    (https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/staging-bucket)).
                    This field requires a Cloud Storage bucket name, not a gs://... URI to a Cloud
                    Storage bucket.""",
                    is_required=False,
                ),
                "tempBucket": Field(
                    String,
                    description="""Optional. A Cloud Storage bucket used to store ephemeral cluster
                    and jobs data, such as Spark and MapReduce history files. If you do not specify
                    a temp bucket, Dataproc will determine a Cloud Storage location (US, ASIA, or
                    EU) for your cluster\'s temp bucket according to the Compute Engine zone where
                    your cluster is deployed, and then create and manage this project-level,
                    per-location bucket. The default bucket has a TTL of 90 days, but you can use
                    any TTL (or none) if you specify a bucket (see Dataproc staging and temp buckets
                    (https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/staging-bucket)).
                    This field requires a Cloud Storage bucket name, not a gs://... URI to a Cloud
                    Storage bucket.""",
                    is_required=False,
                ),
                "gceClusterConfig": Field(
                    Shape(
                        fields={
                            "zoneUri": Field(
                                String,
                                description="""Optional. The Compute Engine zone where the Dataproc
                                cluster will be located. If omitted, the service will pick a zone in
                                the cluster\'s Compute Engine region. On a get request, zone will
                                always be present.A full URL, partial URI, or short name are valid.
                                Examples:
                                https://www.googleapis.com/compute/v1/projects/[project_id]/zones/[zone]
                                projects/[project_id]/zones/[zone] [zone]""",
                                is_required=False,
                            ),
                            "networkUri": Field(
                                String,
                                description="""Optional. The Compute Engine network to be used for
                                machine communications. Cannot be specified with subnetwork_uri. If
                                neither network_uri nor subnetwork_uri is specified, the "default"
                                network of the project is used, if it exists. Cannot be a "Custom
                                Subnet Network" (see Using Subnetworks
                                (https://cloud.google.com/compute/docs/subnetworks) for more
                                information).A full URL, partial URI, or short name are valid.
                                Examples:
                                https://www.googleapis.com/compute/v1/projects/[project_id]/global/networks/default
                                projects/[project_id]/global/networks/default default""",
                                is_required=False,
                            ),
                            "subnetworkUri": Field(
                                String,
                                description="""Optional. The Compute Engine subnetwork to be used
                                for machine communications. Cannot be specified with network_uri.A
                                full URL, partial URI, or short name are valid. Examples:
                                https://www.googleapis.com/compute/v1/projects/[project_id]/regions/[region]/subnetworks/sub0
                                projects/[project_id]/regions/[region]/subnetworks/sub0 sub0""",
                                is_required=False,
                            ),
                            "internalIpOnly": Field(
                                Bool,
                                description="""Optional. This setting applies to subnetwork-enabled
                                networks. It is set to true by default in clusters created with
                                image versions 2.2.x.When set to true: All cluster VMs have internal
                                IP addresses. Google Private Access
                                (https://cloud.google.com/vpc/docs/private-google-access) must be
                                enabled to access Dataproc and other Google Cloud APIs. Off-cluster
                                dependencies must be configured to be accessible without external IP
                                addresses.When set to false: Cluster VMs are not restricted to
                                internal IP addresses. Ephemeral external IP addresses are assigned
                                to each cluster VM.""",
                                is_required=False,
                            ),
                            "privateIpv6GoogleAccess": Field(
                                PrivateIpv6GoogleAccess,
                                description="""Optional. The type of IPv6 access for a cluster.""",
                                is_required=False,
                            ),
                            "serviceAccount": Field(
                                String,
                                description="""Optional. The Dataproc service account
                                (https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/service-accounts#service_accounts_in_dataproc)
                                (also see VM Data Plane identity
                                (https://cloud.google.com/dataproc/docs/concepts/iam/dataproc-principals#vm_service_account_data_plane_identity))
                                used by Dataproc cluster VM instances to access Google Cloud
                                Platform services.If not specified, the Compute Engine default
                                service account
                                (https://cloud.google.com/compute/docs/access/service-accounts#default_service_account)
                                is used.""",
                                is_required=False,
                            ),
                            "serviceAccountScopes": Field(
                                [String],
                                description="""Optional. The URIs of service account scopes to be
                                included in Compute Engine instances. The following base set of
                                scopes is always included:
                                https://www.googleapis.com/auth/cloud.useraccounts.readonly
                                https://www.googleapis.com/auth/devstorage.read_write
                                https://www.googleapis.com/auth/logging.writeIf no scopes are
                                specified, the following defaults are also provided:
                                https://www.googleapis.com/auth/bigquery
                                https://www.googleapis.com/auth/bigtable.admin.table
                                https://www.googleapis.com/auth/bigtable.data
                                https://www.googleapis.com/auth/devstorage.full_control""",
                                is_required=False,
                            ),
                            "tags": Field(
                                [String],
                                description="""The Compute Engine network tags to add to all
                                instances (see Tagging instances
                                (https://cloud.google.com/vpc/docs/add-remove-network-tags)).""",
                                is_required=False,
                            ),
                            "metadata": Field(
                                Permissive(),
                                description="""Optional. The Compute Engine metadata entries to add
                                to all instances (see Project and instance metadata
                                (https://cloud.google.com/compute/docs/storing-retrieving-metadata#project_and_instance_metadata)).""",
                                is_required=False,
                            ),
                            "reservationAffinity": Field(
                                Shape(
                                    fields={
                                        "consumeReservationType": Field(
                                            ConsumeReservationType,
                                            description="""Optional. Type of reservation to
                                            consume""",
                                            is_required=False,
                                        ),
                                        "key": Field(
                                            String,
                                            description="""Optional. Corresponds to the label key of
                                            reservation resource.""",
                                            is_required=False,
                                        ),
                                        "values": Field(
                                            [String],
                                            description="""Optional. Corresponds to the label values
                                            of reservation resource.""",
                                            is_required=False,
                                        ),
                                    },
                                ),
                                description="""Reservation Affinity for consuming Zonal
                                reservation.""",
                                is_required=False,
                            ),
                            "nodeGroupAffinity": Field(
                                Shape(
                                    fields={
                                        "nodeGroupUri": Field(
                                            String,
                                            description="""Required. The URI of a sole-tenant node
                                            group resource
                                            (https://cloud.google.com/compute/docs/reference/rest/v1/nodeGroups)
                                            that the cluster will be created on.A full URL, partial
                                            URI, or node group name are valid. Examples:
                                            https://www.googleapis.com/compute/v1/projects/[project_id]/zones/[zone]/nodeGroups/node-group-1
                                            projects/[project_id]/zones/[zone]/nodeGroups/node-group-1
                                            node-group-1""",
                                            is_required=True,
                                        ),
                                    },
                                ),
                                description="""Node Group Affinity for clusters using sole-tenant
                                node groups. The Dataproc NodeGroupAffinity resource is not related
                                to the Dataproc NodeGroup resource.""",
                                is_required=False,
                            ),
                            "shieldedInstanceConfig": Field(
                                Shape(
                                    fields={
                                        "enableSecureBoot": Field(
                                            Bool,
                                            description="""Optional. Defines whether instances have
                                            Secure Boot enabled.""",
                                            is_required=False,
                                        ),
                                        "enableVtpm": Field(
                                            Bool,
                                            description="""Optional. Defines whether instances have
                                            the vTPM enabled.""",
                                            is_required=False,
                                        ),
                                        "enableIntegrityMonitoring": Field(
                                            Bool,
                                            description="""Optional. Defines whether instances have
                                            integrity monitoring enabled.""",
                                            is_required=False,
                                        ),
                                    },
                                ),
                                description="""Shielded Instance Config for clusters using Compute
                                Engine Shielded VMs
                                (https://cloud.google.com/security/shielded-cloud/shielded-vm).""",
                                is_required=False,
                            ),
                            "confidentialInstanceConfig": Field(
                                Shape(
                                    fields={
                                        "enableConfidentialCompute": Field(
                                            Bool,
                                            description="""Optional. Defines whether the instance
                                            should have confidential compute enabled.""",
                                            is_required=False,
                                        ),
                                    },
                                ),
                                description="""Confidential Instance Config for clusters using
                                Confidential VMs
                                (https://cloud.google.com/compute/confidential-vm/docs)""",
                                is_required=False,
                            ),
                            "resourceManagerTags": Field(
                                Permissive(),
                                description="""Optional. Resource manager tags
                                (https://cloud.google.com/resource-manager/docs/tags/tags-creating-and-managing)
                                to add to all instances (see Use secure tags in Dataproc
                                (https://cloud.google.com/dataproc/docs/guides/attach-secure-tags)).""",
                                is_required=False,
                            ),
                        },
                    ),
                    description="""Common config settings for resources of Compute Engine cluster
                    instances, applicable to all instances in the cluster.""",
                    is_required=False,
                ),
                "masterConfig": Field(
                    Shape(
                        fields={
                            "numInstances": Field(
                                Int,
                                description="""Optional. The number of VM instances in the instance
                                group. For HA cluster master_config groups, must be set to 3. For
                                standard cluster master_config groups, must be set to 1.""",
                                is_required=False,
                            ),
                            "imageUri": Field(
                                String,
                                description="""Optional. The Compute Engine image resource used for
                                cluster instances.The URI can represent an image or image
                                family.Image examples:
                                https://www.googleapis.com/compute/v1/projects/[project_id]/global/images/[image-id]
                                projects/[project_id]/global/images/[image-id] image-idImage family
                                examples. Dataproc will use the most recent image from the family:
                                https://www.googleapis.com/compute/v1/projects/[project_id]/global/images/family/[custom-image-family-name]
                                projects/[project_id]/global/images/family/[custom-image-family-name]If
                                the URI is unspecified, it will be inferred from
                                SoftwareConfig.image_version or the system default.""",
                                is_required=False,
                            ),
                            "machineTypeUri": Field(
                                String,
                                description="""Optional. The Compute Engine machine type used for
                                cluster instances.A full URL, partial URI, or short name are valid.
                                Examples:
                                https://www.googleapis.com/compute/v1/projects/[project_id]/zones/[zone]/machineTypes/n1-standard-2
                                projects/[project_id]/zones/[zone]/machineTypes/n1-standard-2
                                n1-standard-2Auto Zone Exception: If you are using the Dataproc Auto
                                Zone Placement
                                (https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/auto-zone#using_auto_zone_placement)
                                feature, you must use the short name of the machine type resource,
                                for example, n1-standard-2.""",
                                is_required=False,
                            ),
                            "diskConfig": Field(
                                Shape(
                                    fields={
                                        "bootDiskType": Field(
                                            String,
                                            description="""Optional. Type of the boot disk (default
                                            is "pd-standard"). Valid values: "pd-balanced"
                                            (Persistent Disk Balanced Solid State Drive), "pd-ssd"
                                            (Persistent Disk Solid State Drive), or "pd-standard"
                                            (Persistent Disk Hard Disk Drive). See Disk types
                                            (https://cloud.google.com/compute/docs/disks#disk-types).""",
                                            is_required=False,
                                        ),
                                        "bootDiskSizeGb": Field(
                                            Int,
                                            description="""Optional. Size in GB of the boot disk
                                            (default is 500GB).""",
                                            is_required=False,
                                        ),
                                        "numLocalSsds": Field(
                                            Int,
                                            description="""Optional. Number of attached SSDs, from 0
                                            to 8 (default is 0). If SSDs are not attached, the boot
                                            disk is used to store runtime logs and HDFS
                                            (https://hadoop.apache.org/docs/r1.2.1/hdfs_user_guide.html)
                                            data. If one or more SSDs are attached, this runtime
                                            bulk data is spread across them, and the boot disk
                                            contains only basic config and installed binaries.Note:
                                            Local SSD options may vary by machine type and number of
                                            vCPUs selected.""",
                                            is_required=False,
                                        ),
                                        "localSsdInterface": Field(
                                            String,
                                            description="""Optional. Interface type of local SSDs
                                            (default is "scsi"). Valid values: "scsi" (Small
                                            Computer System Interface), "nvme" (Non-Volatile Memory
                                            Express). See local SSD performance
                                            (https://cloud.google.com/compute/docs/disks/local-ssd#performance).""",
                                            is_required=False,
                                        ),
                                        "bootDiskProvisionedIops": Field(
                                            String,
                                            description="""Optional. Indicates how many IOPS to
                                            provision for the disk. This sets the number of I/O
                                            operations per second that the disk can handle. This
                                            field is supported only if boot_disk_type is
                                            hyperdisk-balanced.""",
                                            is_required=False,
                                        ),
                                        "bootDiskProvisionedThroughput": Field(
                                            String,
                                            description="""Optional. Indicates how much throughput
                                            to provision for the disk. This sets the number of
                                            throughput mb per second that the disk can handle.
                                            Values must be greater than or equal to 1. This field is
                                            supported only if boot_disk_type is
                                            hyperdisk-balanced.""",
                                            is_required=False,
                                        ),
                                    },
                                ),
                                description="""Specifies the config of disk options for a group of
                                VM instances.""",
                                is_required=False,
                            ),
                            "preemptibility": Field(
                                Preemptibility,
                                description="""Optional. Specifies the preemptibility of the
                                instance group.The default value for master and worker groups is
                                NON_PREEMPTIBLE. This default cannot be changed.The default value
                                for secondary instances is PREEMPTIBLE.""",
                                is_required=False,
                            ),
                            "managedGroupConfig": Field(
                                Shape(
                                    fields={},
                                ),
                                description="""Specifies the resources used to actively manage an
                                instance group.""",
                                is_required=False,
                            ),
                            "accelerators": Field(
                                [
                                    Shape(
                                        fields={
                                            "acceleratorTypeUri": Field(
                                                String,
                                                description="""Full URL, partial URI, or short name of
                                            the accelerator type resource to expose to this
                                            instance. See Compute Engine AcceleratorTypes
                                            (https://cloud.google.com/compute/docs/reference/v1/acceleratorTypes).Examples:
                                            https://www.googleapis.com/compute/v1/projects/[project_id]/zones/[zone]/acceleratorTypes/nvidia-tesla-t4
                                            projects/[project_id]/zones/[zone]/acceleratorTypes/nvidia-tesla-t4
                                            nvidia-tesla-t4Auto Zone Exception: If you are using the
                                            Dataproc Auto Zone Placement
                                            (https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/auto-zone#using_auto_zone_placement)
                                            feature, you must use the short name of the accelerator
                                            type resource, for example, nvidia-tesla-t4.""",
                                                is_required=False,
                                            ),
                                            "acceleratorCount": Field(
                                                Int,
                                                description="""The number of the accelerator cards of
                                            this type exposed to this instance.""",
                                                is_required=False,
                                            ),
                                        },
                                    )
                                ],
                                description="""Optional. The Compute Engine accelerator
                                configuration for these instances.""",
                                is_required=False,
                            ),
                            "minCpuPlatform": Field(
                                String,
                                description="""Optional. Specifies the minimum cpu platform for the
                                Instance Group. See Dataproc -> Minimum CPU Platform
                                (https://cloud.google.com/dataproc/docs/concepts/compute/dataproc-min-cpu).""",
                                is_required=False,
                            ),
                            "minNumInstances": Field(
                                Int,
                                description="""Optional. The minimum number of primary worker
                                instances to create. If min_num_instances is set, cluster creation
                                will succeed if the number of primary workers created is at least
                                equal to the min_num_instances number.Example: Cluster creation
                                request with num_instances = 5 and min_num_instances = 3: If 4 VMs
                                are created and 1 instance fails, the failed VM is deleted. The
                                cluster is resized to 4 instances and placed in a RUNNING state. If
                                2 instances are created and 3 instances fail, the cluster in placed
                                in an ERROR state. The failed VMs are not deleted.""",
                                is_required=False,
                            ),
                            "instanceFlexibilityPolicy": Field(
                                Shape(
                                    fields={
                                        "provisioningModelMix": Field(
                                            Shape(
                                                fields={
                                                    "standardCapacityBase": Field(
                                                        Int,
                                                        description="""Optional. The base capacity
                                                        that will always use Standard VMs to avoid
                                                        risk of more preemption than the minimum
                                                        capacity you need. Dataproc will create only
                                                        standard VMs until it reaches
                                                        standard_capacity_base, then it will start
                                                        using standard_capacity_percent_above_base
                                                        to mix Spot with Standard VMs. eg. If 15
                                                        instances are requested and
                                                        standard_capacity_base is 5, Dataproc will
                                                        create 5 standard VMs and then start mixing
                                                        spot and standard VMs for remaining 10
                                                        instances.""",
                                                        is_required=False,
                                                    ),
                                                    "standardCapacityPercentAboveBase": Field(
                                                        Int,
                                                        description="""Optional. The percentage of
                                                        target capacity that should use Standard VM.
                                                        The remaining percentage will use Spot VMs.
                                                        The percentage applies only to the capacity
                                                        above standard_capacity_base. eg. If 15
                                                        instances are requested and
                                                        standard_capacity_base is 5 and
                                                        standard_capacity_percent_above_base is 30,
                                                        Dataproc will create 5 standard VMs and then
                                                        start mixing spot and standard VMs for
                                                        remaining 10 instances. The mix will be 30%
                                                        standard and 70% spot.""",
                                                        is_required=False,
                                                    ),
                                                },
                                            ),
                                            description="""Defines how Dataproc should create VMs
                                            with a mixture of provisioning models.""",
                                            is_required=False,
                                        ),
                                        "instanceSelectionList": Field(
                                            [
                                                Shape(
                                                    fields={
                                                        "machineTypes": Field(
                                                            [String],
                                                            description="""Optional. Full machine-type
                                                        names, e.g. "n1-standard-16".""",
                                                            is_required=False,
                                                        ),
                                                        "rank": Field(
                                                            Int,
                                                            description="""Optional. Preference of this
                                                        instance selection. Lower number means
                                                        higher preference. Dataproc will first try
                                                        to create a VM based on the machine-type
                                                        with priority rank and fallback to next rank
                                                        based on availability. Machine types and
                                                        instance selections with the same priority
                                                        have the same preference.""",
                                                            is_required=False,
                                                        ),
                                                    },
                                                )
                                            ],
                                            description="""Optional. List of instance selection
                                            options that the group will use when creating new
                                            VMs.""",
                                            is_required=False,
                                        ),
                                    },
                                ),
                                description="""Instance flexibility Policy allowing a mixture of VM
                                shapes and provisioning models.""",
                                is_required=False,
                            ),
                            "startupConfig": Field(
                                Shape(
                                    fields={
                                        "requiredRegistrationFraction": Field(
                                            Int,
                                            description="""Optional. The config setting to enable
                                            cluster creation/ updation to be successful only after
                                            required_registration_fraction of instances are up and
                                            running. This configuration is applicable to only
                                            secondary workers for now. The cluster will fail if
                                            required_registration_fraction of instances are not
                                            available. This will include instance creation, agent
                                            registration, and service registration (if enabled).""",
                                            is_required=False,
                                        ),
                                    },
                                ),
                                description="""Configuration to handle the startup of instances
                                during cluster create and update process.""",
                                is_required=False,
                            ),
                        },
                    ),
                    description="""The config settings for Compute Engine resources in an instance
                    group, such as a master or worker group.""",
                    is_required=False,
                ),
                "workerConfig": Field(
                    Shape(
                        fields={
                            "numInstances": Field(
                                Int,
                                description="""Optional. The number of VM instances in the instance
                                group. For HA cluster master_config groups, must be set to 3. For
                                standard cluster master_config groups, must be set to 1.""",
                                is_required=False,
                            ),
                            "imageUri": Field(
                                String,
                                description="""Optional. The Compute Engine image resource used for
                                cluster instances.The URI can represent an image or image
                                family.Image examples:
                                https://www.googleapis.com/compute/v1/projects/[project_id]/global/images/[image-id]
                                projects/[project_id]/global/images/[image-id] image-idImage family
                                examples. Dataproc will use the most recent image from the family:
                                https://www.googleapis.com/compute/v1/projects/[project_id]/global/images/family/[custom-image-family-name]
                                projects/[project_id]/global/images/family/[custom-image-family-name]If
                                the URI is unspecified, it will be inferred from
                                SoftwareConfig.image_version or the system default.""",
                                is_required=False,
                            ),
                            "machineTypeUri": Field(
                                String,
                                description="""Optional. The Compute Engine machine type used for
                                cluster instances.A full URL, partial URI, or short name are valid.
                                Examples:
                                https://www.googleapis.com/compute/v1/projects/[project_id]/zones/[zone]/machineTypes/n1-standard-2
                                projects/[project_id]/zones/[zone]/machineTypes/n1-standard-2
                                n1-standard-2Auto Zone Exception: If you are using the Dataproc Auto
                                Zone Placement
                                (https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/auto-zone#using_auto_zone_placement)
                                feature, you must use the short name of the machine type resource,
                                for example, n1-standard-2.""",
                                is_required=False,
                            ),
                            "diskConfig": Field(
                                Shape(
                                    fields={
                                        "bootDiskType": Field(
                                            String,
                                            description="""Optional. Type of the boot disk (default
                                            is "pd-standard"). Valid values: "pd-balanced"
                                            (Persistent Disk Balanced Solid State Drive), "pd-ssd"
                                            (Persistent Disk Solid State Drive), or "pd-standard"
                                            (Persistent Disk Hard Disk Drive). See Disk types
                                            (https://cloud.google.com/compute/docs/disks#disk-types).""",
                                            is_required=False,
                                        ),
                                        "bootDiskSizeGb": Field(
                                            Int,
                                            description="""Optional. Size in GB of the boot disk
                                            (default is 500GB).""",
                                            is_required=False,
                                        ),
                                        "numLocalSsds": Field(
                                            Int,
                                            description="""Optional. Number of attached SSDs, from 0
                                            to 8 (default is 0). If SSDs are not attached, the boot
                                            disk is used to store runtime logs and HDFS
                                            (https://hadoop.apache.org/docs/r1.2.1/hdfs_user_guide.html)
                                            data. If one or more SSDs are attached, this runtime
                                            bulk data is spread across them, and the boot disk
                                            contains only basic config and installed binaries.Note:
                                            Local SSD options may vary by machine type and number of
                                            vCPUs selected.""",
                                            is_required=False,
                                        ),
                                        "localSsdInterface": Field(
                                            String,
                                            description="""Optional. Interface type of local SSDs
                                            (default is "scsi"). Valid values: "scsi" (Small
                                            Computer System Interface), "nvme" (Non-Volatile Memory
                                            Express). See local SSD performance
                                            (https://cloud.google.com/compute/docs/disks/local-ssd#performance).""",
                                            is_required=False,
                                        ),
                                        "bootDiskProvisionedIops": Field(
                                            String,
                                            description="""Optional. Indicates how many IOPS to
                                            provision for the disk. This sets the number of I/O
                                            operations per second that the disk can handle. This
                                            field is supported only if boot_disk_type is
                                            hyperdisk-balanced.""",
                                            is_required=False,
                                        ),
                                        "bootDiskProvisionedThroughput": Field(
                                            String,
                                            description="""Optional. Indicates how much throughput
                                            to provision for the disk. This sets the number of
                                            throughput mb per second that the disk can handle.
                                            Values must be greater than or equal to 1. This field is
                                            supported only if boot_disk_type is
                                            hyperdisk-balanced.""",
                                            is_required=False,
                                        ),
                                    },
                                ),
                                description="""Specifies the config of disk options for a group of
                                VM instances.""",
                                is_required=False,
                            ),
                            "preemptibility": Field(
                                Preemptibility,
                                description="""Optional. Specifies the preemptibility of the
                                instance group.The default value for master and worker groups is
                                NON_PREEMPTIBLE. This default cannot be changed.The default value
                                for secondary instances is PREEMPTIBLE.""",
                                is_required=False,
                            ),
                            "managedGroupConfig": Field(
                                Shape(
                                    fields={},
                                ),
                                description="""Specifies the resources used to actively manage an
                                instance group.""",
                                is_required=False,
                            ),
                            "accelerators": Field(
                                [
                                    Shape(
                                        fields={
                                            "acceleratorTypeUri": Field(
                                                String,
                                                description="""Full URL, partial URI, or short name of
                                            the accelerator type resource to expose to this
                                            instance. See Compute Engine AcceleratorTypes
                                            (https://cloud.google.com/compute/docs/reference/v1/acceleratorTypes).Examples:
                                            https://www.googleapis.com/compute/v1/projects/[project_id]/zones/[zone]/acceleratorTypes/nvidia-tesla-t4
                                            projects/[project_id]/zones/[zone]/acceleratorTypes/nvidia-tesla-t4
                                            nvidia-tesla-t4Auto Zone Exception: If you are using the
                                            Dataproc Auto Zone Placement
                                            (https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/auto-zone#using_auto_zone_placement)
                                            feature, you must use the short name of the accelerator
                                            type resource, for example, nvidia-tesla-t4.""",
                                                is_required=False,
                                            ),
                                            "acceleratorCount": Field(
                                                Int,
                                                description="""The number of the accelerator cards of
                                            this type exposed to this instance.""",
                                                is_required=False,
                                            ),
                                        },
                                    )
                                ],
                                description="""Optional. The Compute Engine accelerator
                                configuration for these instances.""",
                                is_required=False,
                            ),
                            "minCpuPlatform": Field(
                                String,
                                description="""Optional. Specifies the minimum cpu platform for the
                                Instance Group. See Dataproc -> Minimum CPU Platform
                                (https://cloud.google.com/dataproc/docs/concepts/compute/dataproc-min-cpu).""",
                                is_required=False,
                            ),
                            "minNumInstances": Field(
                                Int,
                                description="""Optional. The minimum number of primary worker
                                instances to create. If min_num_instances is set, cluster creation
                                will succeed if the number of primary workers created is at least
                                equal to the min_num_instances number.Example: Cluster creation
                                request with num_instances = 5 and min_num_instances = 3: If 4 VMs
                                are created and 1 instance fails, the failed VM is deleted. The
                                cluster is resized to 4 instances and placed in a RUNNING state. If
                                2 instances are created and 3 instances fail, the cluster in placed
                                in an ERROR state. The failed VMs are not deleted.""",
                                is_required=False,
                            ),
                            "instanceFlexibilityPolicy": Field(
                                Shape(
                                    fields={
                                        "provisioningModelMix": Field(
                                            Shape(
                                                fields={
                                                    "standardCapacityBase": Field(
                                                        Int,
                                                        description="""Optional. The base capacity
                                                        that will always use Standard VMs to avoid
                                                        risk of more preemption than the minimum
                                                        capacity you need. Dataproc will create only
                                                        standard VMs until it reaches
                                                        standard_capacity_base, then it will start
                                                        using standard_capacity_percent_above_base
                                                        to mix Spot with Standard VMs. eg. If 15
                                                        instances are requested and
                                                        standard_capacity_base is 5, Dataproc will
                                                        create 5 standard VMs and then start mixing
                                                        spot and standard VMs for remaining 10
                                                        instances.""",
                                                        is_required=False,
                                                    ),
                                                    "standardCapacityPercentAboveBase": Field(
                                                        Int,
                                                        description="""Optional. The percentage of
                                                        target capacity that should use Standard VM.
                                                        The remaining percentage will use Spot VMs.
                                                        The percentage applies only to the capacity
                                                        above standard_capacity_base. eg. If 15
                                                        instances are requested and
                                                        standard_capacity_base is 5 and
                                                        standard_capacity_percent_above_base is 30,
                                                        Dataproc will create 5 standard VMs and then
                                                        start mixing spot and standard VMs for
                                                        remaining 10 instances. The mix will be 30%
                                                        standard and 70% spot.""",
                                                        is_required=False,
                                                    ),
                                                },
                                            ),
                                            description="""Defines how Dataproc should create VMs
                                            with a mixture of provisioning models.""",
                                            is_required=False,
                                        ),
                                        "instanceSelectionList": Field(
                                            [
                                                Shape(
                                                    fields={
                                                        "machineTypes": Field(
                                                            [String],
                                                            description="""Optional. Full machine-type
                                                        names, e.g. "n1-standard-16".""",
                                                            is_required=False,
                                                        ),
                                                        "rank": Field(
                                                            Int,
                                                            description="""Optional. Preference of this
                                                        instance selection. Lower number means
                                                        higher preference. Dataproc will first try
                                                        to create a VM based on the machine-type
                                                        with priority rank and fallback to next rank
                                                        based on availability. Machine types and
                                                        instance selections with the same priority
                                                        have the same preference.""",
                                                            is_required=False,
                                                        ),
                                                    },
                                                )
                                            ],
                                            description="""Optional. List of instance selection
                                            options that the group will use when creating new
                                            VMs.""",
                                            is_required=False,
                                        ),
                                    },
                                ),
                                description="""Instance flexibility Policy allowing a mixture of VM
                                shapes and provisioning models.""",
                                is_required=False,
                            ),
                            "startupConfig": Field(
                                Shape(
                                    fields={
                                        "requiredRegistrationFraction": Field(
                                            Int,
                                            description="""Optional. The config setting to enable
                                            cluster creation/ updation to be successful only after
                                            required_registration_fraction of instances are up and
                                            running. This configuration is applicable to only
                                            secondary workers for now. The cluster will fail if
                                            required_registration_fraction of instances are not
                                            available. This will include instance creation, agent
                                            registration, and service registration (if enabled).""",
                                            is_required=False,
                                        ),
                                    },
                                ),
                                description="""Configuration to handle the startup of instances
                                during cluster create and update process.""",
                                is_required=False,
                            ),
                        },
                    ),
                    description="""The config settings for Compute Engine resources in an instance
                    group, such as a master or worker group.""",
                    is_required=False,
                ),
                "secondaryWorkerConfig": Field(
                    Shape(
                        fields={
                            "numInstances": Field(
                                Int,
                                description="""Optional. The number of VM instances in the instance
                                group. For HA cluster master_config groups, must be set to 3. For
                                standard cluster master_config groups, must be set to 1.""",
                                is_required=False,
                            ),
                            "imageUri": Field(
                                String,
                                description="""Optional. The Compute Engine image resource used for
                                cluster instances.The URI can represent an image or image
                                family.Image examples:
                                https://www.googleapis.com/compute/v1/projects/[project_id]/global/images/[image-id]
                                projects/[project_id]/global/images/[image-id] image-idImage family
                                examples. Dataproc will use the most recent image from the family:
                                https://www.googleapis.com/compute/v1/projects/[project_id]/global/images/family/[custom-image-family-name]
                                projects/[project_id]/global/images/family/[custom-image-family-name]If
                                the URI is unspecified, it will be inferred from
                                SoftwareConfig.image_version or the system default.""",
                                is_required=False,
                            ),
                            "machineTypeUri": Field(
                                String,
                                description="""Optional. The Compute Engine machine type used for
                                cluster instances.A full URL, partial URI, or short name are valid.
                                Examples:
                                https://www.googleapis.com/compute/v1/projects/[project_id]/zones/[zone]/machineTypes/n1-standard-2
                                projects/[project_id]/zones/[zone]/machineTypes/n1-standard-2
                                n1-standard-2Auto Zone Exception: If you are using the Dataproc Auto
                                Zone Placement
                                (https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/auto-zone#using_auto_zone_placement)
                                feature, you must use the short name of the machine type resource,
                                for example, n1-standard-2.""",
                                is_required=False,
                            ),
                            "diskConfig": Field(
                                Shape(
                                    fields={
                                        "bootDiskType": Field(
                                            String,
                                            description="""Optional. Type of the boot disk (default
                                            is "pd-standard"). Valid values: "pd-balanced"
                                            (Persistent Disk Balanced Solid State Drive), "pd-ssd"
                                            (Persistent Disk Solid State Drive), or "pd-standard"
                                            (Persistent Disk Hard Disk Drive). See Disk types
                                            (https://cloud.google.com/compute/docs/disks#disk-types).""",
                                            is_required=False,
                                        ),
                                        "bootDiskSizeGb": Field(
                                            Int,
                                            description="""Optional. Size in GB of the boot disk
                                            (default is 500GB).""",
                                            is_required=False,
                                        ),
                                        "numLocalSsds": Field(
                                            Int,
                                            description="""Optional. Number of attached SSDs, from 0
                                            to 8 (default is 0). If SSDs are not attached, the boot
                                            disk is used to store runtime logs and HDFS
                                            (https://hadoop.apache.org/docs/r1.2.1/hdfs_user_guide.html)
                                            data. If one or more SSDs are attached, this runtime
                                            bulk data is spread across them, and the boot disk
                                            contains only basic config and installed binaries.Note:
                                            Local SSD options may vary by machine type and number of
                                            vCPUs selected.""",
                                            is_required=False,
                                        ),
                                        "localSsdInterface": Field(
                                            String,
                                            description="""Optional. Interface type of local SSDs
                                            (default is "scsi"). Valid values: "scsi" (Small
                                            Computer System Interface), "nvme" (Non-Volatile Memory
                                            Express). See local SSD performance
                                            (https://cloud.google.com/compute/docs/disks/local-ssd#performance).""",
                                            is_required=False,
                                        ),
                                        "bootDiskProvisionedIops": Field(
                                            String,
                                            description="""Optional. Indicates how many IOPS to
                                            provision for the disk. This sets the number of I/O
                                            operations per second that the disk can handle. This
                                            field is supported only if boot_disk_type is
                                            hyperdisk-balanced.""",
                                            is_required=False,
                                        ),
                                        "bootDiskProvisionedThroughput": Field(
                                            String,
                                            description="""Optional. Indicates how much throughput
                                            to provision for the disk. This sets the number of
                                            throughput mb per second that the disk can handle.
                                            Values must be greater than or equal to 1. This field is
                                            supported only if boot_disk_type is
                                            hyperdisk-balanced.""",
                                            is_required=False,
                                        ),
                                    },
                                ),
                                description="""Specifies the config of disk options for a group of
                                VM instances.""",
                                is_required=False,
                            ),
                            "preemptibility": Field(
                                Preemptibility,
                                description="""Optional. Specifies the preemptibility of the
                                instance group.The default value for master and worker groups is
                                NON_PREEMPTIBLE. This default cannot be changed.The default value
                                for secondary instances is PREEMPTIBLE.""",
                                is_required=False,
                            ),
                            "managedGroupConfig": Field(
                                Shape(
                                    fields={},
                                ),
                                description="""Specifies the resources used to actively manage an
                                instance group.""",
                                is_required=False,
                            ),
                            "accelerators": Field(
                                [
                                    Shape(
                                        fields={
                                            "acceleratorTypeUri": Field(
                                                String,
                                                description="""Full URL, partial URI, or short name of
                                            the accelerator type resource to expose to this
                                            instance. See Compute Engine AcceleratorTypes
                                            (https://cloud.google.com/compute/docs/reference/v1/acceleratorTypes).Examples:
                                            https://www.googleapis.com/compute/v1/projects/[project_id]/zones/[zone]/acceleratorTypes/nvidia-tesla-t4
                                            projects/[project_id]/zones/[zone]/acceleratorTypes/nvidia-tesla-t4
                                            nvidia-tesla-t4Auto Zone Exception: If you are using the
                                            Dataproc Auto Zone Placement
                                            (https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/auto-zone#using_auto_zone_placement)
                                            feature, you must use the short name of the accelerator
                                            type resource, for example, nvidia-tesla-t4.""",
                                                is_required=False,
                                            ),
                                            "acceleratorCount": Field(
                                                Int,
                                                description="""The number of the accelerator cards of
                                            this type exposed to this instance.""",
                                                is_required=False,
                                            ),
                                        },
                                    )
                                ],
                                description="""Optional. The Compute Engine accelerator
                                configuration for these instances.""",
                                is_required=False,
                            ),
                            "minCpuPlatform": Field(
                                String,
                                description="""Optional. Specifies the minimum cpu platform for the
                                Instance Group. See Dataproc -> Minimum CPU Platform
                                (https://cloud.google.com/dataproc/docs/concepts/compute/dataproc-min-cpu).""",
                                is_required=False,
                            ),
                            "minNumInstances": Field(
                                Int,
                                description="""Optional. The minimum number of primary worker
                                instances to create. If min_num_instances is set, cluster creation
                                will succeed if the number of primary workers created is at least
                                equal to the min_num_instances number.Example: Cluster creation
                                request with num_instances = 5 and min_num_instances = 3: If 4 VMs
                                are created and 1 instance fails, the failed VM is deleted. The
                                cluster is resized to 4 instances and placed in a RUNNING state. If
                                2 instances are created and 3 instances fail, the cluster in placed
                                in an ERROR state. The failed VMs are not deleted.""",
                                is_required=False,
                            ),
                            "instanceFlexibilityPolicy": Field(
                                Shape(
                                    fields={
                                        "provisioningModelMix": Field(
                                            Shape(
                                                fields={
                                                    "standardCapacityBase": Field(
                                                        Int,
                                                        description="""Optional. The base capacity
                                                        that will always use Standard VMs to avoid
                                                        risk of more preemption than the minimum
                                                        capacity you need. Dataproc will create only
                                                        standard VMs until it reaches
                                                        standard_capacity_base, then it will start
                                                        using standard_capacity_percent_above_base
                                                        to mix Spot with Standard VMs. eg. If 15
                                                        instances are requested and
                                                        standard_capacity_base is 5, Dataproc will
                                                        create 5 standard VMs and then start mixing
                                                        spot and standard VMs for remaining 10
                                                        instances.""",
                                                        is_required=False,
                                                    ),
                                                    "standardCapacityPercentAboveBase": Field(
                                                        Int,
                                                        description="""Optional. The percentage of
                                                        target capacity that should use Standard VM.
                                                        The remaining percentage will use Spot VMs.
                                                        The percentage applies only to the capacity
                                                        above standard_capacity_base. eg. If 15
                                                        instances are requested and
                                                        standard_capacity_base is 5 and
                                                        standard_capacity_percent_above_base is 30,
                                                        Dataproc will create 5 standard VMs and then
                                                        start mixing spot and standard VMs for
                                                        remaining 10 instances. The mix will be 30%
                                                        standard and 70% spot.""",
                                                        is_required=False,
                                                    ),
                                                },
                                            ),
                                            description="""Defines how Dataproc should create VMs
                                            with a mixture of provisioning models.""",
                                            is_required=False,
                                        ),
                                        "instanceSelectionList": Field(
                                            [
                                                Shape(
                                                    fields={
                                                        "machineTypes": Field(
                                                            [String],
                                                            description="""Optional. Full machine-type
                                                        names, e.g. "n1-standard-16".""",
                                                            is_required=False,
                                                        ),
                                                        "rank": Field(
                                                            Int,
                                                            description="""Optional. Preference of this
                                                        instance selection. Lower number means
                                                        higher preference. Dataproc will first try
                                                        to create a VM based on the machine-type
                                                        with priority rank and fallback to next rank
                                                        based on availability. Machine types and
                                                        instance selections with the same priority
                                                        have the same preference.""",
                                                            is_required=False,
                                                        ),
                                                    },
                                                )
                                            ],
                                            description="""Optional. List of instance selection
                                            options that the group will use when creating new
                                            VMs.""",
                                            is_required=False,
                                        ),
                                    },
                                ),
                                description="""Instance flexibility Policy allowing a mixture of VM
                                shapes and provisioning models.""",
                                is_required=False,
                            ),
                            "startupConfig": Field(
                                Shape(
                                    fields={
                                        "requiredRegistrationFraction": Field(
                                            Int,
                                            description="""Optional. The config setting to enable
                                            cluster creation/ updation to be successful only after
                                            required_registration_fraction of instances are up and
                                            running. This configuration is applicable to only
                                            secondary workers for now. The cluster will fail if
                                            required_registration_fraction of instances are not
                                            available. This will include instance creation, agent
                                            registration, and service registration (if enabled).""",
                                            is_required=False,
                                        ),
                                    },
                                ),
                                description="""Configuration to handle the startup of instances
                                during cluster create and update process.""",
                                is_required=False,
                            ),
                        },
                    ),
                    description="""The config settings for Compute Engine resources in an instance
                    group, such as a master or worker group.""",
                    is_required=False,
                ),
                "softwareConfig": Field(
                    Shape(
                        fields={
                            "imageVersion": Field(
                                String,
                                description="""Optional. The version of software inside the cluster.
                                It must be one of the supported Dataproc Versions
                                (https://cloud.google.com/dataproc/docs/concepts/versioning/dataproc-versions#supported-dataproc-image-versions),
                                such as "1.2" (including a subminor version, such as "1.2.29"), or
                                the "preview" version
                                (https://cloud.google.com/dataproc/docs/concepts/versioning/dataproc-versions#other_versions).
                                If unspecified, it defaults to the latest Debian version.""",
                                is_required=False,
                            ),
                            "properties": Field(
                                Permissive(),
                                description="""Optional. The properties to set on daemon config
                                files.Property keys are specified in prefix:property format, for
                                example core:hadoop.tmp.dir. The following are supported prefixes
                                and their mappings: capacity-scheduler: capacity-scheduler.xml core:
                                core-site.xml distcp: distcp-default.xml hdfs: hdfs-site.xml hive:
                                hive-site.xml mapred: mapred-site.xml pig: pig.properties spark:
                                spark-defaults.conf yarn: yarn-site.xmlFor more information, see
                                Cluster properties
                                (https://cloud.google.com/dataproc/docs/concepts/cluster-properties).""",
                                is_required=False,
                            ),
                            "optionalComponents": Field(
                                [Component],
                                description="""Optional. The set of components to activate on the
                                cluster.""",
                                is_required=False,
                            ),
                        },
                    ),
                    description="""Specifies the selection and config of software inside the
                    cluster.""",
                    is_required=False,
                ),
                "initializationActions": Field(
                    [
                        Shape(
                            fields={
                                "executableFile": Field(
                                    String,
                                    description="""Required. Cloud Storage URI of executable file.""",
                                    is_required=True,
                                ),
                                "executionTimeout": Field(
                                    String,
                                    description="""Optional. Amount of time executable has to complete.
                                Default is 10 minutes (see JSON representation of Duration
                                (https://developers.google.com/protocol-buffers/docs/proto3#json)).Cluster
                                creation fails with an explanatory error message (the name of the
                                executable that caused the error and the exceeded timeout period) if
                                the executable is not completed at end of the timeout period.""",
                                    is_required=False,
                                ),
                            },
                        )
                    ],
                    description="""Optional. Commands to execute on each node after config is
                    completed. By default, executables are run on master and all worker nodes. You
                    can test a node\'s role metadata to run an executable on a master or worker
                    node, as shown below using curl (you can also use wget): ROLE=$(curl -H
                    Metadata-Flavor:Google
                    http://metadata/computeMetadata/v1/instance/attributes/dataproc-role) if [[
                    "${ROLE}" == \'Master\' ]]; then ... master specific actions ... else ... worker
                    specific actions ... fi """,
                    is_required=False,
                ),
                "encryptionConfig": Field(
                    Shape(
                        fields={
                            "gcePdKmsKeyName": Field(
                                String,
                                description="""Optional. The Cloud KMS key resource name to use for
                                persistent disk encryption for all instances in the cluster. See Use
                                CMEK with cluster data
                                (https://cloud.google.com//dataproc/docs/concepts/configuring-clusters/customer-managed-encryption#use_cmek_with_cluster_data)
                                for more information.""",
                                is_required=False,
                            ),
                            "kmsKey": Field(
                                String,
                                description="""Optional. The Cloud KMS key resource name to use for
                                cluster persistent disk and job argument encryption. See Use CMEK
                                with cluster data
                                (https://cloud.google.com//dataproc/docs/concepts/configuring-clusters/customer-managed-encryption#use_cmek_with_cluster_data)
                                for more information.When this key resource name is provided, the
                                following job arguments of the following job types submitted to the
                                cluster are encrypted using CMEK: FlinkJob args
                                (https://cloud.google.com/dataproc/docs/reference/rest/v1/FlinkJob)
                                HadoopJob args
                                (https://cloud.google.com/dataproc/docs/reference/rest/v1/HadoopJob)
                                SparkJob args
                                (https://cloud.google.com/dataproc/docs/reference/rest/v1/SparkJob)
                                SparkRJob args
                                (https://cloud.google.com/dataproc/docs/reference/rest/v1/SparkRJob)
                                PySparkJob args
                                (https://cloud.google.com/dataproc/docs/reference/rest/v1/PySparkJob)
                                SparkSqlJob
                                (https://cloud.google.com/dataproc/docs/reference/rest/v1/SparkSqlJob)
                                scriptVariables and queryList.queries HiveJob
                                (https://cloud.google.com/dataproc/docs/reference/rest/v1/HiveJob)
                                scriptVariables and queryList.queries PigJob
                                (https://cloud.google.com/dataproc/docs/reference/rest/v1/PigJob)
                                scriptVariables and queryList.queries PrestoJob
                                (https://cloud.google.com/dataproc/docs/reference/rest/v1/PrestoJob)
                                scriptVariables and queryList.queries""",
                                is_required=False,
                            ),
                        },
                    ),
                    description="""Encryption settings for the cluster.""",
                    is_required=False,
                ),
                "autoscalingConfig": Field(
                    Shape(
                        fields={
                            "policyUri": Field(
                                String,
                                description="""Optional. The autoscaling policy used by the
                                cluster.Only resource names including projectid and location
                                (region) are valid. Examples:
                                https://www.googleapis.com/compute/v1/projects/[project_id]/locations/[dataproc_region]/autoscalingPolicies/[policy_id]
                                projects/[project_id]/locations/[dataproc_region]/autoscalingPolicies/[policy_id]Note
                                that the policy must be in the same project and Dataproc region.""",
                                is_required=False,
                            ),
                        },
                    ),
                    description="""Autoscaling Policy config associated with the cluster.""",
                    is_required=False,
                ),
                "securityConfig": Field(
                    Shape(
                        fields={
                            "kerberosConfig": Field(
                                Shape(
                                    fields={
                                        "enableKerberos": Field(
                                            Bool,
                                            description="""Optional. Flag to indicate whether to
                                            Kerberize the cluster (default: false). Set this field
                                            to true to enable Kerberos on a cluster.""",
                                            is_required=False,
                                        ),
                                        "rootPrincipalPasswordUri": Field(
                                            String,
                                            description="""Optional. The Cloud Storage URI of a KMS
                                            encrypted file containing the root principal
                                            password.""",
                                            is_required=False,
                                        ),
                                        "kmsKeyUri": Field(
                                            String,
                                            description="""Optional. The URI of the KMS key used to
                                            encrypt sensitive files.""",
                                            is_required=False,
                                        ),
                                        "keystoreUri": Field(
                                            String,
                                            description="""Optional. The Cloud Storage URI of the
                                            keystore file used for SSL encryption. If not provided,
                                            Dataproc will provide a self-signed certificate.""",
                                            is_required=False,
                                        ),
                                        "truststoreUri": Field(
                                            String,
                                            description="""Optional. The Cloud Storage URI of the
                                            truststore file used for SSL encryption. If not
                                            provided, Dataproc will provide a self-signed
                                            certificate.""",
                                            is_required=False,
                                        ),
                                        "keystorePasswordUri": Field(
                                            String,
                                            description="""Optional. The Cloud Storage URI of a KMS
                                            encrypted file containing the password to the user
                                            provided keystore. For the self-signed certificate, this
                                            password is generated by Dataproc.""",
                                            is_required=False,
                                        ),
                                        "keyPasswordUri": Field(
                                            String,
                                            description="""Optional. The Cloud Storage URI of a KMS
                                            encrypted file containing the password to the user
                                            provided key. For the self-signed certificate, this
                                            password is generated by Dataproc.""",
                                            is_required=False,
                                        ),
                                        "truststorePasswordUri": Field(
                                            String,
                                            description="""Optional. The Cloud Storage URI of a KMS
                                            encrypted file containing the password to the user
                                            provided truststore. For the self-signed certificate,
                                            this password is generated by Dataproc.""",
                                            is_required=False,
                                        ),
                                        "crossRealmTrustRealm": Field(
                                            String,
                                            description="""Optional. The remote realm the Dataproc
                                            on-cluster KDC will trust, should the user enable cross
                                            realm trust.""",
                                            is_required=False,
                                        ),
                                        "crossRealmTrustKdc": Field(
                                            String,
                                            description="""Optional. The KDC (IP or hostname) for
                                            the remote trusted realm in a cross realm trust
                                            relationship.""",
                                            is_required=False,
                                        ),
                                        "crossRealmTrustAdminServer": Field(
                                            String,
                                            description="""Optional. The admin server (IP or
                                            hostname) for the remote trusted realm in a cross realm
                                            trust relationship.""",
                                            is_required=False,
                                        ),
                                        "crossRealmTrustSharedPasswordUri": Field(
                                            String,
                                            description="""Optional. The Cloud Storage URI of a KMS
                                            encrypted file containing the shared password between
                                            the on-cluster Kerberos realm and the remote trusted
                                            realm, in a cross realm trust relationship.""",
                                            is_required=False,
                                        ),
                                        "kdcDbKeyUri": Field(
                                            String,
                                            description="""Optional. The Cloud Storage URI of a KMS
                                            encrypted file containing the master key of the KDC
                                            database.""",
                                            is_required=False,
                                        ),
                                        "tgtLifetimeHours": Field(
                                            Int,
                                            description="""Optional. The lifetime of the ticket
                                            granting ticket, in hours. If not specified, or user
                                            specifies 0, then default value 10 will be used.""",
                                            is_required=False,
                                        ),
                                        "realm": Field(
                                            String,
                                            description="""Optional. The name of the on-cluster
                                            Kerberos realm. If not specified, the uppercased domain
                                            of hostnames will be the realm.""",
                                            is_required=False,
                                        ),
                                    },
                                ),
                                description="""Specifies Kerberos related configuration.""",
                                is_required=False,
                            ),
                            "identityConfig": Field(
                                Shape(
                                    fields={
                                        "userServiceAccountMapping": Field(
                                            Permissive(),
                                            description="""Required. Map of user to service
                                            account.""",
                                            is_required=True,
                                        ),
                                    },
                                ),
                                description="""Identity related configuration, including service
                                account based secure multi-tenancy user mappings.""",
                                is_required=False,
                            ),
                        },
                    ),
                    description="""Security related configuration, including encryption, Kerberos,
                    etc.""",
                    is_required=False,
                ),
                "lifecycleConfig": Field(
                    Shape(
                        fields={
                            "idleDeleteTtl": Field(
                                String,
                                description="""Optional. The duration to keep the cluster alive
                                while idling (when no jobs are running). Passing this threshold will
                                cause the cluster to be deleted. Minimum value is 5 minutes; maximum
                                value is 14 days (see JSON representation of Duration
                                (https://developers.google.com/protocol-buffers/docs/proto3#json)).""",
                                is_required=False,
                            ),
                            "autoDeleteTime": Field(
                                String,
                                description="""Optional. The time when cluster will be auto-deleted
                                (see JSON representation of Timestamp
                                (https://developers.google.com/protocol-buffers/docs/proto3#json)).""",
                                is_required=False,
                            ),
                            "autoDeleteTtl": Field(
                                String,
                                description="""Optional. The lifetime duration of cluster. The
                                cluster will be auto-deleted at the end of this period. Minimum
                                value is 10 minutes; maximum value is 14 days (see JSON
                                representation of Duration
                                (https://developers.google.com/protocol-buffers/docs/proto3#json)).""",
                                is_required=False,
                            ),
                        },
                    ),
                    description="""Specifies the cluster auto-delete schedule configuration.""",
                    is_required=False,
                ),
                "endpointConfig": Field(
                    Shape(
                        fields={
                            "enableHttpPortAccess": Field(
                                Bool,
                                description="""Optional. If true, enable http access to specific
                                ports on the cluster from external sources. Defaults to false.""",
                                is_required=False,
                            ),
                        },
                    ),
                    description="""Endpoint config for this cluster""",
                    is_required=False,
                ),
                "metastoreConfig": Field(
                    Shape(
                        fields={
                            "dataprocMetastoreService": Field(
                                String,
                                description="""Required. Resource name of an existing Dataproc
                                Metastore service.Example:
                                projects/[project_id]/locations/[dataproc_region]/services/[service-name]""",
                                is_required=True,
                            ),
                        },
                    ),
                    description="""Specifies a Metastore configuration.""",
                    is_required=False,
                ),
                "gkeClusterConfig": Field(
                    Shape(
                        fields={
                            "namespacedGkeDeploymentTarget": Field(
                                Shape(
                                    fields={
                                        "targetGkeCluster": Field(
                                            String,
                                            description="""Optional. The target GKE cluster to
                                            deploy to. Format:
                                            \'projects/{project}/locations/{location}/clusters/{cluster_id}\'""",
                                            is_required=False,
                                        ),
                                        "clusterNamespace": Field(
                                            String,
                                            description="""Optional. A namespace within the GKE
                                            cluster to deploy into.""",
                                            is_required=False,
                                        ),
                                    },
                                ),
                                description="""Deprecated. Used only for the deprecated beta. A
                                full, namespace-isolated deployment target for an existing GKE
                                cluster.""",
                                is_required=False,
                            ),
                            "gkeClusterTarget": Field(
                                String,
                                description="""Optional. A target GKE cluster to deploy to. It must
                                be in the same project and region as the Dataproc cluster (the GKE
                                cluster can be zonal or regional). Format:
                                \'projects/{project}/locations/{location}/clusters/{cluster_id}\'""",
                                is_required=False,
                            ),
                            "nodePoolTarget": Field(
                                [
                                    Shape(
                                        fields={
                                            "nodePool": Field(
                                                String,
                                                description="""Required. The target GKE node pool.
                                            Format:
                                            \'projects/{project}/locations/{location}/clusters/{cluster}/nodePools/{node_pool}\'""",
                                                is_required=True,
                                            ),
                                            "roles": Field(
                                                [Component],
                                                description="""Required. The roles associated with the
                                            GKE node pool.""",
                                                is_required=True,
                                            ),
                                            "nodePoolConfig": Field(
                                                Shape(
                                                    fields={
                                                        "config": Field(
                                                            Shape(
                                                                fields={
                                                                    "machineType": Field(
                                                                        String,
                                                                        description="""Optional. The
                                                                    name of a Compute Engine machine
                                                                    type
                                                                    (https://cloud.google.com/compute/docs/machine-types).""",
                                                                        is_required=False,
                                                                    ),
                                                                    "localSsdCount": Field(
                                                                        Int,
                                                                        description="""Optional. The
                                                                    number of local SSD disks to
                                                                    attach to the node, which is
                                                                    limited by the maximum number of
                                                                    disks allowable per zone (see
                                                                    Adding Local SSDs
                                                                    (https://cloud.google.com/compute/docs/disks/local-ssd)).""",
                                                                        is_required=False,
                                                                    ),
                                                                    "preemptible": Field(
                                                                        Bool,
                                                                        description="""Optional. Whether
                                                                    the nodes are created as legacy
                                                                    preemptible VM instances
                                                                    (https://cloud.google.com/compute/docs/instances/preemptible).
                                                                    Also see Spot VMs, preemptible
                                                                    VM instances without a maximum
                                                                    lifetime. Legacy and Spot
                                                                    preemptible nodes cannot be used
                                                                    in a node pool with the
                                                                    CONTROLLER role or in the
                                                                    DEFAULT node pool if the
                                                                    CONTROLLER role is not assigned
                                                                    (the DEFAULT node pool will
                                                                    assume the CONTROLLER role).""",
                                                                        is_required=False,
                                                                    ),
                                                                    "accelerators": Field(
                                                                        [
                                                                            Shape(
                                                                                fields={
                                                                                    "acceleratorCount": Field(
                                                                                        String,
                                                                                        description="""The
                                                                                number of
                                                                                accelerator cards
                                                                                exposed to an
                                                                                instance.""",
                                                                                        is_required=False,
                                                                                    ),
                                                                                    "acceleratorType": Field(
                                                                                        String,
                                                                                        description="""The
                                                                                accelerator type
                                                                                resource namename
                                                                                (see GPUs on Compute
                                                                                Engine).""",
                                                                                        is_required=False,
                                                                                    ),
                                                                                    "gpuPartitionSize": Field(
                                                                                        String,
                                                                                        description="""Size
                                                                                of partitions to
                                                                                create on the GPU.
                                                                                Valid values are
                                                                                described in the
                                                                                NVIDIA mig user
                                                                                guide
                                                                                (https://docs.nvidia.com/datacenter/tesla/mig-user-guide/#partitioning).""",
                                                                                        is_required=False,
                                                                                    ),
                                                                                },
                                                                            )
                                                                        ],
                                                                        description="""Optional. A list
                                                                    of hardware accelerators
                                                                    (https://cloud.google.com/compute/docs/gpus)
                                                                    to attach to each node.""",
                                                                        is_required=False,
                                                                    ),
                                                                    "minCpuPlatform": Field(
                                                                        String,
                                                                        description="""Optional. Minimum
                                                                    CPU platform
                                                                    (https://cloud.google.com/compute/docs/instances/specify-min-cpu-platform)
                                                                    to be used by this instance. The
                                                                    instance may be scheduled on the
                                                                    specified or a newer CPU
                                                                    platform. Specify the friendly
                                                                    names of CPU platforms, such as
                                                                    "Intel Haswell"` or Intel Sandy
                                                                    Bridge".""",
                                                                        is_required=False,
                                                                    ),
                                                                    "bootDiskKmsKey": Field(
                                                                        String,
                                                                        description="""Optional. The
                                                                    Customer Managed Encryption Key
                                                                    (CMEK)
                                                                    (https://cloud.google.com/kubernetes-engine/docs/how-to/using-cmek)
                                                                    used to encrypt the boot disk
                                                                    attached to each node in the
                                                                    node pool. Specify the key using
                                                                    the following format:
                                                                    projects/{project}/locations/{location}/keyRings/{key_ring}/cryptoKeys/{crypto_key}""",
                                                                        is_required=False,
                                                                    ),
                                                                    "spot": Field(
                                                                        Bool,
                                                                        description="""Optional. Whether
                                                                    the nodes are created as Spot VM
                                                                    instances
                                                                    (https://cloud.google.com/compute/docs/instances/spot).
                                                                    Spot VMs are the latest update
                                                                    to legacy preemptible VMs. Spot
                                                                    VMs do not have a maximum
                                                                    lifetime. Legacy and Spot
                                                                    preemptible nodes cannot be used
                                                                    in a node pool with the
                                                                    CONTROLLER role or in the
                                                                    DEFAULT node pool if the
                                                                    CONTROLLER role is not assigned
                                                                    (the DEFAULT node pool will
                                                                    assume the CONTROLLER role).""",
                                                                        is_required=False,
                                                                    ),
                                                                },
                                                            ),
                                                            description="""Parameters that describe
                                                        cluster nodes.""",
                                                            is_required=False,
                                                        ),
                                                        "locations": Field(
                                                            [String],
                                                            description="""Optional. The list of Compute
                                                        Engine zones
                                                        (https://cloud.google.com/compute/docs/zones#available)
                                                        where node pool nodes associated with a
                                                        Dataproc on GKE virtual cluster will be
                                                        located.Note: All node pools associated with
                                                        a virtual cluster must be located in the
                                                        same region as the virtual cluster, and they
                                                        must be located in the same zone within that
                                                        region.If a location is not specified during
                                                        node pool creation, Dataproc on GKE will
                                                        choose the zone.""",
                                                            is_required=False,
                                                        ),
                                                        "autoscaling": Field(
                                                            Shape(
                                                                fields={
                                                                    "minNodeCount": Field(
                                                                        Int,
                                                                        description="""The minimum
                                                                    number of nodes in the node
                                                                    pool. Must be >= 0 and <=
                                                                    max_node_count.""",
                                                                        is_required=False,
                                                                    ),
                                                                    "maxNodeCount": Field(
                                                                        Int,
                                                                        description="""The maximum
                                                                    number of nodes in the node
                                                                    pool. Must be >= min_node_count,
                                                                    and must be > 0. Note: Quota
                                                                    must be sufficient to scale up
                                                                    the cluster.""",
                                                                        is_required=False,
                                                                    ),
                                                                },
                                                            ),
                                                            description="""GkeNodePoolAutoscaling
                                                        contains information the cluster autoscaler
                                                        needs to adjust the size of the node pool to
                                                        the current cluster usage.""",
                                                            is_required=False,
                                                        ),
                                                    },
                                                ),
                                                description="""The configuration of a GKE node pool used
                                            by a Dataproc-on-GKE cluster
                                            (https://cloud.google.com/dataproc/docs/concepts/jobs/dataproc-gke#create-a-dataproc-on-gke-cluster).""",
                                                is_required=False,
                                            ),
                                        },
                                    )
                                ],
                                description="""Optional. GKE node pools where workloads will be
                                scheduled. At least one node pool must be assigned the DEFAULT
                                GkeNodePoolTarget.Role. If a GkeNodePoolTarget is not specified,
                                Dataproc constructs a DEFAULT GkeNodePoolTarget. Each role can be
                                given to only one GkeNodePoolTarget. All node pools must have the
                                same location settings.""",
                                is_required=False,
                            ),
                        },
                    ),
                    description="""The cluster\'s GKE config.""",
                    is_required=False,
                ),
                "dataprocMetricConfig": Field(
                    Shape(
                        fields={
                            "metrics": Field(
                                [
                                    Shape(
                                        fields={
                                            "metricSource": Field(
                                                MetricSource,
                                                description="""Required. A standard set of metrics is
                                            collected unless metricOverrides are specified for the
                                            metric source (see Custom metrics
                                            (https://cloud.google.com/dataproc/docs/guides/dataproc-metrics#custom_metrics)
                                            for more information).""",
                                                is_required=True,
                                            ),
                                            "metricOverrides": Field(
                                                [String],
                                                description="""Optional. Specify one or more Custom
                                            metrics
                                            (https://cloud.google.com/dataproc/docs/guides/dataproc-metrics#custom_metrics)
                                            to collect for the metric course (for the SPARK metric
                                            source (any Spark metric
                                            (https://spark.apache.org/docs/latest/monitoring.html#metrics)
                                            can be specified).Provide metrics in the following
                                            format: METRIC_SOURCE: INSTANCE:GROUP:METRIC Use
                                            camelcase as appropriate.Examples:
                                            yarn:ResourceManager:QueueMetrics:AppsCompleted
                                            spark:driver:DAGScheduler:job.allJobs
                                            sparkHistoryServer:JVM:Memory:NonHeapMemoryUsage.committed
                                            hiveserver2:JVM:Memory:NonHeapMemoryUsage.used Notes:
                                            Only the specified overridden metrics are collected for
                                            the metric source. For example, if one or more
                                            spark:executive metrics are listed as metric overrides,
                                            other SPARK metrics are not collected. The collection of
                                            the metrics for other enabled custom metric sources is
                                            unaffected. For example, if both SPARK and YARN metric
                                            sources are enabled, and overrides are provided for
                                            Spark metrics only, all YARN metrics are collected.""",
                                                is_required=False,
                                            ),
                                        },
                                    )
                                ],
                                description="""Required. Metrics sources to enable.""",
                                is_required=True,
                            ),
                        },
                    ),
                    description="""Dataproc metric config.""",
                    is_required=False,
                ),
                "auxiliaryNodeGroups": Field(
                    [
                        Shape(
                            fields={
                                "nodeGroup": Field(
                                    Shape(
                                        fields={
                                            "name": Field(
                                                String,
                                                description="""The Node group resource name
                                            (https://aip.dev/122).""",
                                                is_required=False,
                                            ),
                                            "roles": Field(
                                                [Component],
                                                description="""Required. Node group roles.""",
                                                is_required=True,
                                            ),
                                            "nodeGroupConfig": Field(
                                                Shape(
                                                    fields={
                                                        "numInstances": Field(
                                                            Int,
                                                            description="""Optional. The number of VM
                                                        instances in the instance group. For HA
                                                        cluster master_config groups, must be set to
                                                        3. For standard cluster master_config
                                                        groups, must be set to 1.""",
                                                            is_required=False,
                                                        ),
                                                        "imageUri": Field(
                                                            String,
                                                            description="""Optional. The Compute Engine
                                                        image resource used for cluster
                                                        instances.The URI can represent an image or
                                                        image family.Image examples:
                                                        https://www.googleapis.com/compute/v1/projects/[project_id]/global/images/[image-id]
                                                        projects/[project_id]/global/images/[image-id]
                                                        image-idImage family examples. Dataproc will
                                                        use the most recent image from the family:
                                                        https://www.googleapis.com/compute/v1/projects/[project_id]/global/images/family/[custom-image-family-name]
                                                        projects/[project_id]/global/images/family/[custom-image-family-name]If
                                                        the URI is unspecified, it will be inferred
                                                        from SoftwareConfig.image_version or the
                                                        system default.""",
                                                            is_required=False,
                                                        ),
                                                        "machineTypeUri": Field(
                                                            String,
                                                            description="""Optional. The Compute Engine
                                                        machine type used for cluster instances.A
                                                        full URL, partial URI, or short name are
                                                        valid. Examples:
                                                        https://www.googleapis.com/compute/v1/projects/[project_id]/zones/[zone]/machineTypes/n1-standard-2
                                                        projects/[project_id]/zones/[zone]/machineTypes/n1-standard-2
                                                        n1-standard-2Auto Zone Exception: If you are
                                                        using the Dataproc Auto Zone Placement
                                                        (https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/auto-zone#using_auto_zone_placement)
                                                        feature, you must use the short name of the
                                                        machine type resource, for example,
                                                        n1-standard-2.""",
                                                            is_required=False,
                                                        ),
                                                        "diskConfig": Field(
                                                            Shape(
                                                                fields={
                                                                    "bootDiskType": Field(
                                                                        String,
                                                                        description="""Optional. Type of
                                                                    the boot disk (default is
                                                                    "pd-standard"). Valid values:
                                                                    "pd-balanced" (Persistent Disk
                                                                    Balanced Solid State Drive),
                                                                    "pd-ssd" (Persistent Disk Solid
                                                                    State Drive), or "pd-standard"
                                                                    (Persistent Disk Hard Disk
                                                                    Drive). See Disk types
                                                                    (https://cloud.google.com/compute/docs/disks#disk-types).""",
                                                                        is_required=False,
                                                                    ),
                                                                    "bootDiskSizeGb": Field(
                                                                        Int,
                                                                        description="""Optional. Size in
                                                                    GB of the boot disk (default is
                                                                    500GB).""",
                                                                        is_required=False,
                                                                    ),
                                                                    "numLocalSsds": Field(
                                                                        Int,
                                                                        description="""Optional. Number
                                                                    of attached SSDs, from 0 to 8
                                                                    (default is 0). If SSDs are not
                                                                    attached, the boot disk is used
                                                                    to store runtime logs and HDFS
                                                                    (https://hadoop.apache.org/docs/r1.2.1/hdfs_user_guide.html)
                                                                    data. If one or more SSDs are
                                                                    attached, this runtime bulk data
                                                                    is spread across them, and the
                                                                    boot disk contains only basic
                                                                    config and installed
                                                                    binaries.Note: Local SSD options
                                                                    may vary by machine type and
                                                                    number of vCPUs selected.""",
                                                                        is_required=False,
                                                                    ),
                                                                    "localSsdInterface": Field(
                                                                        String,
                                                                        description="""Optional.
                                                                    Interface type of local SSDs
                                                                    (default is "scsi"). Valid
                                                                    values: "scsi" (Small Computer
                                                                    System Interface), "nvme"
                                                                    (Non-Volatile Memory Express).
                                                                    See local SSD performance
                                                                    (https://cloud.google.com/compute/docs/disks/local-ssd#performance).""",
                                                                        is_required=False,
                                                                    ),
                                                                    "bootDiskProvisionedIops": Field(
                                                                        String,
                                                                        description="""Optional.
                                                                    Indicates how many IOPS to
                                                                    provision for the disk. This
                                                                    sets the number of I/O
                                                                    operations per second that the
                                                                    disk can handle. This field is
                                                                    supported only if boot_disk_type
                                                                    is hyperdisk-balanced.""",
                                                                        is_required=False,
                                                                    ),
                                                                    "bootDiskProvisionedThroughput": Field(
                                                                        String,
                                                                        description="""Optional.
                                                                    Indicates how much throughput to
                                                                    provision for the disk. This
                                                                    sets the number of throughput mb
                                                                    per second that the disk can
                                                                    handle. Values must be greater
                                                                    than or equal to 1. This field
                                                                    is supported only if
                                                                    boot_disk_type is
                                                                    hyperdisk-balanced.""",
                                                                        is_required=False,
                                                                    ),
                                                                },
                                                            ),
                                                            description="""Specifies the config of disk
                                                        options for a group of VM instances.""",
                                                            is_required=False,
                                                        ),
                                                        "preemptibility": Field(
                                                            Preemptibility,
                                                            description="""Optional. Specifies the
                                                        preemptibility of the instance group.The
                                                        default value for master and worker groups
                                                        is NON_PREEMPTIBLE. This default cannot be
                                                        changed.The default value for secondary
                                                        instances is PREEMPTIBLE.""",
                                                            is_required=False,
                                                        ),
                                                        "managedGroupConfig": Field(
                                                            Shape(
                                                                fields={},
                                                            ),
                                                            description="""Specifies the resources used
                                                        to actively manage an instance group.""",
                                                            is_required=False,
                                                        ),
                                                        "accelerators": Field(
                                                            [
                                                                Shape(
                                                                    fields={
                                                                        "acceleratorTypeUri": Field(
                                                                            String,
                                                                            description="""Full URL, partial
                                                                    URI, or short name of the
                                                                    accelerator type resource to
                                                                    expose to this instance. See
                                                                    Compute Engine AcceleratorTypes
                                                                    (https://cloud.google.com/compute/docs/reference/v1/acceleratorTypes).Examples:
                                                                    https://www.googleapis.com/compute/v1/projects/[project_id]/zones/[zone]/acceleratorTypes/nvidia-tesla-t4
                                                                    projects/[project_id]/zones/[zone]/acceleratorTypes/nvidia-tesla-t4
                                                                    nvidia-tesla-t4Auto Zone
                                                                    Exception: If you are using the
                                                                    Dataproc Auto Zone Placement
                                                                    (https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/auto-zone#using_auto_zone_placement)
                                                                    feature, you must use the short
                                                                    name of the accelerator type
                                                                    resource, for example,
                                                                    nvidia-tesla-t4.""",
                                                                            is_required=False,
                                                                        ),
                                                                        "acceleratorCount": Field(
                                                                            Int,
                                                                            description="""The number of the
                                                                    accelerator cards of this type
                                                                    exposed to this instance.""",
                                                                            is_required=False,
                                                                        ),
                                                                    },
                                                                )
                                                            ],
                                                            description="""Optional. The Compute Engine
                                                        accelerator configuration for these
                                                        instances.""",
                                                            is_required=False,
                                                        ),
                                                        "minCpuPlatform": Field(
                                                            String,
                                                            description="""Optional. Specifies the
                                                        minimum cpu platform for the Instance Group.
                                                        See Dataproc -> Minimum CPU Platform
                                                        (https://cloud.google.com/dataproc/docs/concepts/compute/dataproc-min-cpu).""",
                                                            is_required=False,
                                                        ),
                                                        "minNumInstances": Field(
                                                            Int,
                                                            description="""Optional. The minimum number
                                                        of primary worker instances to create. If
                                                        min_num_instances is set, cluster creation
                                                        will succeed if the number of primary
                                                        workers created is at least equal to the
                                                        min_num_instances number.Example: Cluster
                                                        creation request with num_instances = 5 and
                                                        min_num_instances = 3: If 4 VMs are created
                                                        and 1 instance fails, the failed VM is
                                                        deleted. The cluster is resized to 4
                                                        instances and placed in a RUNNING state. If
                                                        2 instances are created and 3 instances
                                                        fail, the cluster in placed in an ERROR
                                                        state. The failed VMs are not deleted.""",
                                                            is_required=False,
                                                        ),
                                                        "instanceFlexibilityPolicy": Field(
                                                            Shape(
                                                                fields={
                                                                    "provisioningModelMix": Field(
                                                                        Shape(
                                                                            fields={
                                                                                "standardCapacityBase": Field(
                                                                                    Int,
                                                                                    description="""Optional.
                                                                                The base capacity
                                                                                that will always use
                                                                                Standard VMs to
                                                                                avoid risk of more
                                                                                preemption than the
                                                                                minimum capacity you
                                                                                need. Dataproc will
                                                                                create only standard
                                                                                VMs until it reaches
                                                                                standard_capacity_base,
                                                                                then it will start
                                                                                using
                                                                                standard_capacity_percent_above_base
                                                                                to mix Spot with
                                                                                Standard VMs. eg. If
                                                                                15 instances are
                                                                                requested and
                                                                                standard_capacity_base
                                                                                is 5, Dataproc will
                                                                                create 5 standard
                                                                                VMs and then start
                                                                                mixing spot and
                                                                                standard VMs for
                                                                                remaining 10
                                                                                instances.""",
                                                                                    is_required=False,
                                                                                ),
                                                                                "standardCapacityPercentAboveBase": Field(
                                                                                    Int,
                                                                                    description="""Optional.
                                                                                The percentage of
                                                                                target capacity that
                                                                                should use Standard
                                                                                VM. The remaining
                                                                                percentage will use
                                                                                Spot VMs. The
                                                                                percentage applies
                                                                                only to the capacity
                                                                                above
                                                                                standard_capacity_base.
                                                                                eg. If 15 instances
                                                                                are requested and
                                                                                standard_capacity_base
                                                                                is 5 and
                                                                                standard_capacity_percent_above_base
                                                                                is 30, Dataproc will
                                                                                create 5 standard
                                                                                VMs and then start
                                                                                mixing spot and
                                                                                standard VMs for
                                                                                remaining 10
                                                                                instances. The mix
                                                                                will be 30% standard
                                                                                and 70% spot.""",
                                                                                    is_required=False,
                                                                                ),
                                                                            },
                                                                        ),
                                                                        description="""Defines how
                                                                    Dataproc should create VMs with
                                                                    a mixture of provisioning
                                                                    models.""",
                                                                        is_required=False,
                                                                    ),
                                                                    "instanceSelectionList": Field(
                                                                        [
                                                                            Shape(
                                                                                fields={
                                                                                    "machineTypes": Field(
                                                                                        [String],
                                                                                        description="""Optional.
                                                                                Full machine-type
                                                                                names, e.g.
                                                                                "n1-standard-16".""",
                                                                                        is_required=False,
                                                                                    ),
                                                                                    "rank": Field(
                                                                                        Int,
                                                                                        description="""Optional.
                                                                                Preference of this
                                                                                instance selection.
                                                                                Lower number means
                                                                                higher preference.
                                                                                Dataproc will first
                                                                                try to create a VM
                                                                                based on the
                                                                                machine-type with
                                                                                priority rank and
                                                                                fallback to next
                                                                                rank based on
                                                                                availability.
                                                                                Machine types and
                                                                                instance selections
                                                                                with the same
                                                                                priority have the
                                                                                same preference.""",
                                                                                        is_required=False,
                                                                                    ),
                                                                                },
                                                                            )
                                                                        ],
                                                                        description="""Optional. List of
                                                                    instance selection options that
                                                                    the group will use when creating
                                                                    new VMs.""",
                                                                        is_required=False,
                                                                    ),
                                                                },
                                                            ),
                                                            description="""Instance flexibility Policy
                                                        allowing a mixture of VM shapes and
                                                        provisioning models.""",
                                                            is_required=False,
                                                        ),
                                                        "startupConfig": Field(
                                                            Shape(
                                                                fields={
                                                                    "requiredRegistrationFraction": Field(
                                                                        Int,
                                                                        description="""Optional. The
                                                                    config setting to enable cluster
                                                                    creation/ updation to be
                                                                    successful only after
                                                                    required_registration_fraction
                                                                    of instances are up and running.
                                                                    This configuration is applicable
                                                                    to only secondary workers for
                                                                    now. The cluster will fail if
                                                                    required_registration_fraction
                                                                    of instances are not available.
                                                                    This will include instance
                                                                    creation, agent registration,
                                                                    and service registration (if
                                                                    enabled).""",
                                                                        is_required=False,
                                                                    ),
                                                                },
                                                            ),
                                                            description="""Configuration to handle the
                                                        startup of instances during cluster create
                                                        and update process.""",
                                                            is_required=False,
                                                        ),
                                                    },
                                                ),
                                                description="""The config settings for Compute Engine
                                            resources in an instance group, such as a master or
                                            worker group.""",
                                                is_required=False,
                                            ),
                                            "labels": Field(
                                                Permissive(),
                                                description="""Optional. Node group labels. Label keys
                                            must consist of from 1 to 63 characters and conform to
                                            RFC 1035 (https://www.ietf.org/rfc/rfc1035.txt). Label
                                            values can be empty. If specified, they must consist of
                                            from 1 to 63 characters and conform to RFC 1035
                                            (https://www.ietf.org/rfc/rfc1035.txt). The node group
                                            must have no more than 32 labels.""",
                                                is_required=False,
                                            ),
                                        },
                                    ),
                                    description="""Dataproc Node Group. The Dataproc NodeGroup resource
                                is not related to the Dataproc NodeGroupAffinity resource.""",
                                    is_required=False,
                                ),
                                "nodeGroupId": Field(
                                    String,
                                    description="""Optional. A node group ID. Generated if not
                                specified.The ID must contain only letters (a-z, A-Z), numbers
                                (0-9), underscores (_), and hyphens (-). Cannot begin or end with
                                underscore or hyphen. Must consist of from 3 to 33 characters.""",
                                    is_required=False,
                                ),
                            },
                        )
                    ],
                    description="""Optional. The node group settings.""",
                    is_required=False,
                ),
            },
        ),
        description="""The cluster config.""",
        is_required=False,
    )
