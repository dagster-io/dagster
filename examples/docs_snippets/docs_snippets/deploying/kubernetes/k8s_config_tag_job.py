from dagster import job, op


# fmt: off
@op
def my_op(context):
    context.log.info("running")

# start_k8s_config
@job(
    tags={
        "dagster-k8s/config": {
            "container_config": {
                "resources": {
                    "requests": {"cpu": "250m", "memory": "64Mi"},
                    "limits": {"cpu": "500m", "memory": "2560Mi"},
                },
                "volume_mounts": [
                    {"name": "volume1", "mount_path": "foo/bar", "sub_path": "file.txt"}
                ],
            },
            "pod_template_spec_metadata": {
                "annotations": {"cluster-autoscaler.kubernetes.io/safe-to-evict": "true"}
            },
            "pod_spec_config": {
                "volumes": [{"name": "volume1", "secret": {"secret_name": "volume_secret_name"}}],
                "affinity": {
                    "node_affinity": {
                        "required_during_scheduling_ignored_during_execution": {
                            "node_selector_terms": [
                                {
                                    "match_expressions": [
                                        {
                                            "key": "beta.kubernetes.io/os",
                                            "operator": "In",
                                            "values": ["windows", "linux"],
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                },
            },
        },
    },
)
def my_job():
    my_op()
# end_k8s_config
# fmt: on
