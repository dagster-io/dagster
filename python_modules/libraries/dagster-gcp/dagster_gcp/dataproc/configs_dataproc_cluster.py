"""NOTE: THIS FILE IS AUTO-GENERATED. DO NOT EDIT.

@generated

Produced via:
parse_dataproc_configs.py \

"""


from dagster import Bool, Field, Int, Permissive, Shape, String

from .types_dataproc_cluster import Component


def define_dataproc_cluster_config():
    return Field(
        Shape(
            fields={
                "masterConfig": Field(
                    Shape(
                        fields={
                            "accelerators": Field(
                                [
                                    Shape(
                                        fields={
                                            "acceleratorCount": Field(
                                                Int,
                                                description="""The number of the accelerator cards of
                                            this type exposed to this instance.""",
                                                is_required=False,
                                            ),
                                            "acceleratorTypeUri": Field(
                                                String,
                                                description="""Full URL, partial URI, or short name of
                                            the accelerator type resource to expose to this
                                            instance. See Compute Engine AcceleratorTypes.Examples:
                                            https://www.googleapis.com/compute/beta/projects/[project_id]/zones/us-east1-a/acceleratorTypes/nvidia-tesla-k80
                                            projects/[project_id]/zones/us-east1-a/acceleratorTypes/nvidia-tesla-k80
                                            nvidia-tesla-k80Auto Zone Exception: If you are using
                                            the Cloud Dataproc Auto Zone Placement feature, you must
                                            use the short name of the accelerator type resource, for
                                            example, nvidia-tesla-k80.""",
                                                is_required=False,
                                            ),
                                        }
                                    )
                                ],
                                description="""Optional. The Compute Engine accelerator
                                configuration for these instances.Beta Feature: This feature is
                                still under development. It may be changed before final release.""",
                                is_required=False,
                            ),
                            "numInstances": Field(
                                Int,
                                description="""Optional. The number of VM instances in the instance
                                group. For master instance groups, must be set to 1.""",
                                is_required=False,
                            ),
                            "diskConfig": Field(
                                Shape(
                                    fields={
                                        "numLocalSsds": Field(
                                            Int,
                                            description="""Optional. Number of attached SSDs, from 0
                                            to 4 (default is 0). If SSDs are not attached, the boot
                                            disk is used to store runtime logs and HDFS
                                            (https://hadoop.apache.org/docs/r1.2.1/hdfs_user_guide.html)
                                            data. If one or more SSDs are attached, this runtime
                                            bulk data is spread across them, and the boot disk
                                            contains only basic config and installed binaries.""",
                                            is_required=False,
                                        ),
                                        "bootDiskSizeGb": Field(
                                            Int,
                                            description="""Optional. Size in GB of the boot disk
                                            (default is 500GB).""",
                                            is_required=False,
                                        ),
                                        "bootDiskType": Field(
                                            String,
                                            description="""Optional. Type of the boot disk (default
                                            is "pd-standard"). Valid values: "pd-ssd" (Persistent
                                            Disk Solid State Drive) or "pd-standard" (Persistent
                                            Disk Hard Disk Drive).""",
                                            is_required=False,
                                        ),
                                    }
                                ),
                                description="""Specifies the config of disk options for a group of
                                VM instances.""",
                                is_required=False,
                            ),
                            "managedGroupConfig": Field(
                                Shape(fields={}),
                                description="""Specifies the resources used to actively manage an
                                instance group.""",
                                is_required=False,
                            ),
                            "isPreemptible": Field(
                                Bool,
                                description="""Optional. Specifies that this instance group contains
                                preemptible instances.""",
                                is_required=False,
                            ),
                            "imageUri": Field(
                                String,
                                description="""Optional. The Compute Engine image resource used for
                                cluster instances. It can be specified or may be inferred from
                                SoftwareConfig.image_version.""",
                                is_required=False,
                            ),
                            "machineTypeUri": Field(
                                String,
                                description="""Optional. The Compute Engine machine type used for
                                cluster instances.A full URL, partial URI, or short name are valid.
                                Examples:
                                https://www.googleapis.com/compute/v1/projects/[project_id]/zones/us-east1-a/machineTypes/n1-standard-2
                                projects/[project_id]/zones/us-east1-a/machineTypes/n1-standard-2
                                n1-standard-2Auto Zone Exception: If you are using the Cloud
                                Dataproc Auto Zone Placement feature, you must use the short name of
                                the machine type resource, for example, n1-standard-2.""",
                                is_required=False,
                            ),
                        }
                    ),
                    description="""Optional. The config settings for Compute Engine resources in an
                    instance group, such as a master or worker group.""",
                    is_required=False,
                ),
                "secondaryWorkerConfig": Field(
                    Shape(
                        fields={
                            "accelerators": Field(
                                [
                                    Shape(
                                        fields={
                                            "acceleratorCount": Field(
                                                Int,
                                                description="""The number of the accelerator cards of
                                            this type exposed to this instance.""",
                                                is_required=False,
                                            ),
                                            "acceleratorTypeUri": Field(
                                                String,
                                                description="""Full URL, partial URI, or short name of
                                            the accelerator type resource to expose to this
                                            instance. See Compute Engine AcceleratorTypes.Examples:
                                            https://www.googleapis.com/compute/beta/projects/[project_id]/zones/us-east1-a/acceleratorTypes/nvidia-tesla-k80
                                            projects/[project_id]/zones/us-east1-a/acceleratorTypes/nvidia-tesla-k80
                                            nvidia-tesla-k80Auto Zone Exception: If you are using
                                            the Cloud Dataproc Auto Zone Placement feature, you must
                                            use the short name of the accelerator type resource, for
                                            example, nvidia-tesla-k80.""",
                                                is_required=False,
                                            ),
                                        }
                                    )
                                ],
                                description="""Optional. The Compute Engine accelerator
                                configuration for these instances.Beta Feature: This feature is
                                still under development. It may be changed before final release.""",
                                is_required=False,
                            ),
                            "numInstances": Field(
                                Int,
                                description="""Optional. The number of VM instances in the instance
                                group. For master instance groups, must be set to 1.""",
                                is_required=False,
                            ),
                            "diskConfig": Field(
                                Shape(
                                    fields={
                                        "numLocalSsds": Field(
                                            Int,
                                            description="""Optional. Number of attached SSDs, from 0
                                            to 4 (default is 0). If SSDs are not attached, the boot
                                            disk is used to store runtime logs and HDFS
                                            (https://hadoop.apache.org/docs/r1.2.1/hdfs_user_guide.html)
                                            data. If one or more SSDs are attached, this runtime
                                            bulk data is spread across them, and the boot disk
                                            contains only basic config and installed binaries.""",
                                            is_required=False,
                                        ),
                                        "bootDiskSizeGb": Field(
                                            Int,
                                            description="""Optional. Size in GB of the boot disk
                                            (default is 500GB).""",
                                            is_required=False,
                                        ),
                                        "bootDiskType": Field(
                                            String,
                                            description="""Optional. Type of the boot disk (default
                                            is "pd-standard"). Valid values: "pd-ssd" (Persistent
                                            Disk Solid State Drive) or "pd-standard" (Persistent
                                            Disk Hard Disk Drive).""",
                                            is_required=False,
                                        ),
                                    }
                                ),
                                description="""Specifies the config of disk options for a group of
                                VM instances.""",
                                is_required=False,
                            ),
                            "managedGroupConfig": Field(
                                Shape(fields={}),
                                description="""Specifies the resources used to actively manage an
                                instance group.""",
                                is_required=False,
                            ),
                            "isPreemptible": Field(
                                Bool,
                                description="""Optional. Specifies that this instance group contains
                                preemptible instances.""",
                                is_required=False,
                            ),
                            "imageUri": Field(
                                String,
                                description="""Optional. The Compute Engine image resource used for
                                cluster instances. It can be specified or may be inferred from
                                SoftwareConfig.image_version.""",
                                is_required=False,
                            ),
                            "machineTypeUri": Field(
                                String,
                                description="""Optional. The Compute Engine machine type used for
                                cluster instances.A full URL, partial URI, or short name are valid.
                                Examples:
                                https://www.googleapis.com/compute/v1/projects/[project_id]/zones/us-east1-a/machineTypes/n1-standard-2
                                projects/[project_id]/zones/us-east1-a/machineTypes/n1-standard-2
                                n1-standard-2Auto Zone Exception: If you are using the Cloud
                                Dataproc Auto Zone Placement feature, you must use the short name of
                                the machine type resource, for example, n1-standard-2.""",
                                is_required=False,
                            ),
                        }
                    ),
                    description="""Optional. The config settings for Compute Engine resources in an
                    instance group, such as a master or worker group.""",
                    is_required=False,
                ),
                "encryptionConfig": Field(
                    Shape(
                        fields={
                            "gcePdKmsKeyName": Field(
                                String,
                                description="""Optional. The Cloud KMS key name to use for PD disk
                                encryption for all instances in the cluster.""",
                                is_required=False,
                            )
                        }
                    ),
                    description="""Encryption settings for the cluster.""",
                    is_required=False,
                ),
                "securityConfig": Field(
                    Shape(
                        fields={
                            "kerberosConfig": Field(
                                Shape(
                                    fields={
                                        "truststorePasswordUri": Field(
                                            String,
                                            description="""Optional. The Cloud Storage URI of a KMS
                                            encrypted file containing the password to the user
                                            provided truststore. For the self-signed certificate,
                                            this password is generated by Dataproc.""",
                                            is_required=False,
                                        ),
                                        "enableKerberos": Field(
                                            Bool,
                                            description="""Optional. Flag to indicate whether to
                                            Kerberize the cluster.""",
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
                                        "crossRealmTrustRealm": Field(
                                            String,
                                            description="""Optional. The remote realm the Dataproc
                                            on-cluster KDC will trust, should the user enable cross
                                            realm trust.""",
                                            is_required=False,
                                        ),
                                        "rootPrincipalPasswordUri": Field(
                                            String,
                                            description="""Required. The Cloud Storage URI of a KMS
                                            encrypted file containing the root principal
                                            password.""",
                                            is_required=False,
                                        ),
                                        "kmsKeyUri": Field(
                                            String,
                                            description="""Required. The uri of the KMS key used to
                                            encrypt various sensitive files.""",
                                            is_required=False,
                                        ),
                                        "crossRealmTrustKdc": Field(
                                            String,
                                            description="""Optional. The KDC (IP or hostname) for
                                            the remote trusted realm in a cross realm trust
                                            relationship.""",
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
                                        "tgtLifetimeHours": Field(
                                            Int,
                                            description="""Optional. The lifetime of the ticket
                                            granting ticket, in hours. If not specified, or user
                                            specifies 0, then default value 10 will be used.""",
                                            is_required=False,
                                        ),
                                        "keystoreUri": Field(
                                            String,
                                            description="""Optional. The Cloud Storage URI of the
                                            keystore file used for SSL encryption. If not provided,
                                            Dataproc will provide a self-signed certificate.""",
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
                                        "keystorePasswordUri": Field(
                                            String,
                                            description="""Optional. The Cloud Storage URI of a KMS
                                            encrypted file containing the password to the user
                                            provided keystore. For the self-signed certificate, this
                                            password is generated by Dataproc.""",
                                            is_required=False,
                                        ),
                                        "crossRealmTrustAdminServer": Field(
                                            String,
                                            description="""Optional. The admin server (IP or
                                            hostname) for the remote trusted realm in a cross realm
                                            trust relationship.""",
                                            is_required=False,
                                        ),
                                        "kdcDbKeyUri": Field(
                                            String,
                                            description="""Optional. The Cloud Storage URI of a KMS
                                            encrypted file containing the master key of the KDC
                                            database.""",
                                            is_required=False,
                                        ),
                                    }
                                ),
                                description="""Specifies Kerberos related configuration.""",
                                is_required=False,
                            )
                        }
                    ),
                    description="""Security related configuration, including Kerberos.""",
                    is_required=False,
                ),
                "initializationActions": Field(
                    [
                        Shape(
                            fields={
                                "executionTimeout": Field(
                                    String,
                                    description="""Optional. Amount of time executable has to complete.
                                Default is 10 minutes. Cluster creation fails with an explanatory
                                error message (the name of the executable that caused the error and
                                the exceeded timeout period) if the executable is not completed at
                                end of the timeout period.""",
                                    is_required=False,
                                ),
                                "executableFile": Field(
                                    String,
                                    description="""Required. Cloud Storage URI of executable file.""",
                                    is_required=False,
                                ),
                            }
                        )
                    ],
                    description="""Optional. Commands to execute on each node after config is
                    completed. By default, executables are run on master and all worker nodes. You
                    can test a node\'s role metadata to run an executable on a master or worker
                    node, as shown below using curl (you can also use wget): ROLE=$(curl -H
                    Metadata-Flavor:Google
                    http://metadata/computeMetadata/v1/instance/attributes/dataproc-role) if [[
                    "${ROLE}" == \'Master\' ]]; then   ... master specific actions ... else   ...
                    worker specific actions ... fi """,
                    is_required=False,
                ),
                "configBucket": Field(
                    String,
                    description="""Optional. A Google Cloud Storage bucket used to stage job
                    dependencies, config files, and job driver console output. If you do not specify
                    a staging bucket, Cloud Dataproc will determine a Cloud Storage location (US,
                    ASIA, or EU) for your cluster\'s staging bucket according to the Google Compute
                    Engine zone where your cluster is deployed, and then create and manage this
                    project-level, per-location bucket (see Cloud Dataproc staging bucket).""",
                    is_required=False,
                ),
                "workerConfig": Field(
                    Shape(
                        fields={
                            "accelerators": Field(
                                [
                                    Shape(
                                        fields={
                                            "acceleratorCount": Field(
                                                Int,
                                                description="""The number of the accelerator cards of
                                            this type exposed to this instance.""",
                                                is_required=False,
                                            ),
                                            "acceleratorTypeUri": Field(
                                                String,
                                                description="""Full URL, partial URI, or short name of
                                            the accelerator type resource to expose to this
                                            instance. See Compute Engine AcceleratorTypes.Examples:
                                            https://www.googleapis.com/compute/beta/projects/[project_id]/zones/us-east1-a/acceleratorTypes/nvidia-tesla-k80
                                            projects/[project_id]/zones/us-east1-a/acceleratorTypes/nvidia-tesla-k80
                                            nvidia-tesla-k80Auto Zone Exception: If you are using
                                            the Cloud Dataproc Auto Zone Placement feature, you must
                                            use the short name of the accelerator type resource, for
                                            example, nvidia-tesla-k80.""",
                                                is_required=False,
                                            ),
                                        }
                                    )
                                ],
                                description="""Optional. The Compute Engine accelerator
                                configuration for these instances.Beta Feature: This feature is
                                still under development. It may be changed before final release.""",
                                is_required=False,
                            ),
                            "numInstances": Field(
                                Int,
                                description="""Optional. The number of VM instances in the instance
                                group. For master instance groups, must be set to 1.""",
                                is_required=False,
                            ),
                            "diskConfig": Field(
                                Shape(
                                    fields={
                                        "numLocalSsds": Field(
                                            Int,
                                            description="""Optional. Number of attached SSDs, from 0
                                            to 4 (default is 0). If SSDs are not attached, the boot
                                            disk is used to store runtime logs and HDFS
                                            (https://hadoop.apache.org/docs/r1.2.1/hdfs_user_guide.html)
                                            data. If one or more SSDs are attached, this runtime
                                            bulk data is spread across them, and the boot disk
                                            contains only basic config and installed binaries.""",
                                            is_required=False,
                                        ),
                                        "bootDiskSizeGb": Field(
                                            Int,
                                            description="""Optional. Size in GB of the boot disk
                                            (default is 500GB).""",
                                            is_required=False,
                                        ),
                                        "bootDiskType": Field(
                                            String,
                                            description="""Optional. Type of the boot disk (default
                                            is "pd-standard"). Valid values: "pd-ssd" (Persistent
                                            Disk Solid State Drive) or "pd-standard" (Persistent
                                            Disk Hard Disk Drive).""",
                                            is_required=False,
                                        ),
                                    }
                                ),
                                description="""Specifies the config of disk options for a group of
                                VM instances.""",
                                is_required=False,
                            ),
                            "managedGroupConfig": Field(
                                Shape(fields={}),
                                description="""Specifies the resources used to actively manage an
                                instance group.""",
                                is_required=False,
                            ),
                            "isPreemptible": Field(
                                Bool,
                                description="""Optional. Specifies that this instance group contains
                                preemptible instances.""",
                                is_required=False,
                            ),
                            "imageUri": Field(
                                String,
                                description="""Optional. The Compute Engine image resource used for
                                cluster instances. It can be specified or may be inferred from
                                SoftwareConfig.image_version.""",
                                is_required=False,
                            ),
                            "machineTypeUri": Field(
                                String,
                                description="""Optional. The Compute Engine machine type used for
                                cluster instances.A full URL, partial URI, or short name are valid.
                                Examples:
                                https://www.googleapis.com/compute/v1/projects/[project_id]/zones/us-east1-a/machineTypes/n1-standard-2
                                projects/[project_id]/zones/us-east1-a/machineTypes/n1-standard-2
                                n1-standard-2Auto Zone Exception: If you are using the Cloud
                                Dataproc Auto Zone Placement feature, you must use the short name of
                                the machine type resource, for example, n1-standard-2.""",
                                is_required=False,
                            ),
                        }
                    ),
                    description="""Optional. The config settings for Compute Engine resources in an
                    instance group, such as a master or worker group.""",
                    is_required=False,
                ),
                "gceClusterConfig": Field(
                    Shape(
                        fields={
                            "networkUri": Field(
                                String,
                                description="""Optional. The Compute Engine network to be used for
                                machine communications. Cannot be specified with subnetwork_uri. If
                                neither network_uri nor subnetwork_uri is specified, the "default"
                                network of the project is used, if it exists. Cannot be a "Custom
                                Subnet Network" (see Using Subnetworks for more information).A full
                                URL, partial URI, or short name are valid. Examples:
                                https://www.googleapis.com/compute/v1/projects/[project_id]/regions/global/default
                                projects/[project_id]/regions/global/default default""",
                                is_required=False,
                            ),
                            "zoneUri": Field(
                                String,
                                description="""Optional. The zone where the Compute Engine cluster
                                will be located. On a create request, it is required in the "global"
                                region. If omitted in a non-global Cloud Dataproc region, the
                                service will pick a zone in the corresponding Compute Engine region.
                                On a get request, zone will always be present.A full URL, partial
                                URI, or short name are valid. Examples:
                                https://www.googleapis.com/compute/v1/projects/[project_id]/zones/[zone]
                                projects/[project_id]/zones/[zone] us-central1-f""",
                                is_required=False,
                            ),
                            "metadata": Field(
                                Permissive(),
                                description="""The Compute Engine metadata entries to add to all
                                instances (see Project and instance metadata
                                (https://cloud.google.com/compute/docs/storing-retrieving-metadata#project_and_instance_metadata)).""",
                                is_required=False,
                            ),
                            "internalIpOnly": Field(
                                Bool,
                                description="""Optional. If true, all instances in the cluster will
                                only have internal IP addresses. By default, clusters are not
                                restricted to internal IP addresses, and will have ephemeral
                                external IP addresses assigned to each instance. This
                                internal_ip_only restriction can only be enabled for subnetwork
                                enabled networks, and all off-cluster dependencies must be
                                configured to be accessible without external IP addresses.""",
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
                                description="""The Compute Engine tags to add to all instances (see
                                Tagging instances).""",
                                is_required=False,
                            ),
                            "serviceAccount": Field(
                                String,
                                description="""Optional. The service account of the instances.
                                Defaults to the default Compute Engine service account. Custom
                                service accounts need permissions equivalent to the following IAM
                                roles: roles/logging.logWriter roles/storage.objectAdmin(see
                                https://cloud.google.com/compute/docs/access/service-accounts#custom_service_accounts
                                for more information). Example:
                                [account_id]@[project_id].iam.gserviceaccount.com""",
                                is_required=False,
                            ),
                            "subnetworkUri": Field(
                                String,
                                description="""Optional. The Compute Engine subnetwork to be used
                                for machine communications. Cannot be specified with network_uri.A
                                full URL, partial URI, or short name are valid. Examples:
                                https://www.googleapis.com/compute/v1/projects/[project_id]/regions/us-east1/subnetworks/sub0
                                projects/[project_id]/regions/us-east1/subnetworks/sub0 sub0""",
                                is_required=False,
                            ),
                        }
                    ),
                    description="""Common config settings for resources of Compute Engine cluster
                    instances, applicable to all instances in the cluster.""",
                    is_required=False,
                ),
                "softwareConfig": Field(
                    Shape(
                        fields={
                            "properties": Field(
                                Permissive(),
                                description="""Optional. The properties to set on daemon config
                                files.Property keys are specified in prefix:property format, for
                                example core:hadoop.tmp.dir. The following are supported prefixes
                                and their mappings: capacity-scheduler: capacity-scheduler.xml core:
                                core-site.xml distcp: distcp-default.xml hdfs: hdfs-site.xml hive:
                                hive-site.xml mapred: mapred-site.xml pig: pig.properties spark:
                                spark-defaults.conf yarn: yarn-site.xmlFor more information, see
                                Cluster properties.""",
                                is_required=False,
                            ),
                            "optionalComponents": Field(
                                [Component],
                                description="""The set of optional components to activate on the
                                cluster.""",
                                is_required=False,
                            ),
                            "imageVersion": Field(
                                String,
                                description="""Optional. The version of software inside the cluster.
                                It must be one of the supported Cloud Dataproc Versions, such as
                                "1.2" (including a subminor version, such as "1.2.29"), or the
                                "preview" version. If unspecified, it defaults to the latest Debian
                                version.""",
                                is_required=False,
                            ),
                        }
                    ),
                    description="""Specifies the selection and config of software inside the
                    cluster.""",
                    is_required=False,
                ),
            }
        ),
        description="""The cluster config.""",
        is_required=False,
    )
