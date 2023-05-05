import os
import re
import uuid
from unittest import mock

import httplib2
from dagster import RunConfig, _seven, job
from dagster_gcp import (
    DataprocOpConfig,
    DataprocResource,
    configurable_dataproc_op,
    dataproc_op,
    dataproc_resource,
)

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "default_project")
CLUSTER_NAME = "test-%s" % uuid.uuid4().hex
REGION = "us-west1"

DATAPROC_BASE_URI = "https://dataproc.googleapis.com/v1/projects/{project}/regions/{region}".format(
    project=PROJECT_ID, region=REGION
)
DATAPROC_CLUSTERS_URI = f"{DATAPROC_BASE_URI}/clusters"
DATAPROC_JOBS_URI = f"{DATAPROC_BASE_URI}/jobs"
DATAPROC_SCHEMA_URI = "https://www.googleapis.com/discovery/v1/apis/dataproc/v1/rest"

EXPECTED_RESULTS = [
    # OAuth authorize credentials
    (re.escape("https://oauth2.googleapis.com/token"), "POST", {"access_token": "foo"}),
    # Cluster create
    (re.escape(DATAPROC_CLUSTERS_URI + "?alt=json"), "POST", {}),
    # Cluster get
    (
        re.escape(DATAPROC_CLUSTERS_URI + f"/{CLUSTER_NAME}?alt=json"),
        "GET",
        {"status": {"state": "RUNNING"}},
    ),
    # Jobs submit
    (
        re.escape(DATAPROC_JOBS_URI + ":submit?alt=json"),
        "POST",
        {"reference": {"jobId": "some job ID"}},
    ),
    # Jobs get
    (re.escape(DATAPROC_JOBS_URI) + r".*?\?alt=json", "GET", {"status": {"state": "DONE"}}),
    # Cluster delete
    (re.escape(DATAPROC_CLUSTERS_URI + f"/{CLUSTER_NAME}?alt=json"), "DELETE", {}),
]


class HttpSnooper(httplib2.Http):
    def __init__(self, *args, **kwargs):
        super(HttpSnooper, self).__init__(*args, **kwargs)

    def request(
        self, uri, method="GET", body=None, headers=None, redirections=5, connection_type=None
    ):
        for expected_uri, expected_method, result in EXPECTED_RESULTS:
            if re.match(expected_uri, uri) and method == expected_method:
                return (
                    httplib2.Response({"status": "200"}),
                    _seven.json.dumps(result).encode("utf-8"),
                )

        # Pass this one through since its the entire JSON schema used for dynamic object creation
        if uri == DATAPROC_SCHEMA_URI:
            response, content = super(HttpSnooper, self).request(
                uri,
                method=method,
                body=body,
                headers=headers,
                redirections=redirections,
                connection_type=connection_type,
            )
            return response, content


def test_dataproc_resource():
    """Tests dataproc cluster creation/deletion. Requests are captured by the responses library, so
    no actual HTTP requests are made here.

    Note that inspecting the HTTP requests can be useful for debugging, which can be done by adding:

    import httplib2
    httplib2.debuglevel = 4
    """
    with mock.patch("httplib2.Http", new=HttpSnooper):

        @job(resource_defs={"dataproc": dataproc_resource})
        def test_dataproc():
            dataproc_op()

        result = test_dataproc.execute_in_process(
            run_config={
                "ops": {
                    "dataproc_op": {
                        "config": {
                            "job_config": {
                                "projectId": PROJECT_ID,
                                "region": REGION,
                                "job": {
                                    "reference": {"projectId": PROJECT_ID},
                                    "placement": {"clusterName": CLUSTER_NAME},
                                    "hiveJob": {"queryList": {"queries": ["SHOW DATABASES"]}},
                                },
                            },
                            "job_scoped_cluster": True,
                        }
                    }
                },
                "resources": {
                    "dataproc": {
                        "config": {
                            "projectId": PROJECT_ID,
                            "clusterName": CLUSTER_NAME,
                            "region": REGION,
                            "cluster_config": {
                                "softwareConfig": {
                                    "properties": {
                                        # Create a single-node cluster
                                        # This needs to be the string "true" when
                                        # serialized, not a boolean true
                                        "dataproc:dataproc.allow.zero.workers": "true"
                                    }
                                }
                            },
                        }
                    }
                },
            }
        )
        assert result.success


def test_wait_for_job_with_timeout():
    """Test submitting a job with timeout of 0 second so that it always fails."""
    with mock.patch("httplib2.Http", new=HttpSnooper):

        @job(resource_defs={"dataproc": dataproc_resource})
        def test_dataproc():
            dataproc_op()

        try:
            test_dataproc.execute_in_process(
                run_config={
                    "ops": {
                        "dataproc_op": {
                            "config": {
                                "job_timeout_in_seconds": 0,
                                "job_config": {
                                    "projectId": PROJECT_ID,
                                    "region": REGION,
                                    "job": {
                                        "reference": {"projectId": PROJECT_ID},
                                        "placement": {"clusterName": CLUSTER_NAME},
                                        "hiveJob": {"queryList": {"queries": ["SHOW DATABASES"]}},
                                    },
                                },
                                "job_scoped_cluster": True,
                            }
                        }
                    },
                    "resources": {
                        "dataproc": {
                            "config": {
                                "projectId": PROJECT_ID,
                                "clusterName": CLUSTER_NAME,
                                "region": REGION,
                                "cluster_config": {
                                    "softwareConfig": {
                                        "properties": {
                                            # Create a single-node cluster
                                            # This needs to be the string "true" when
                                            # serialized, not a boolean true
                                            "dataproc:dataproc.allow.zero.workers": "true"
                                        }
                                    }
                                },
                            }
                        }
                    },
                }
            )
            assert False
        except Exception as e:
            assert "Job run timed out" in str(e)


def test_pydantic_dataproc_resource():
    """Tests pydantic dataproc cluster creation/deletion. Requests are captured by the responses library, so
    no actual HTTP requests are made here.

    Note that inspecting the HTTP requests can be useful for debugging, which can be done by adding:

    import httplib2
    httplib2.debuglevel = 4
    """
    with mock.patch("httplib2.Http", new=HttpSnooper):

        @job
        def test_dataproc():
            configurable_dataproc_op()

        result = test_dataproc.execute_in_process(
            run_config=RunConfig(
                ops={
                    "configurable_dataproc_op": DataprocOpConfig(
                        job_scoped_cluster=True,
                        project_id=PROJECT_ID,
                        region=REGION,
                        job_config={
                            "reference": {"projectId": PROJECT_ID},
                            "placement": {"clusterName": CLUSTER_NAME},
                            "hiveJob": {"queryList": {"queries": ["SHOW DATABASES"]}},
                        },
                    )
                },
            ),
            resources={
                "dataproc": DataprocResource(
                    project_id=PROJECT_ID,
                    cluster_name=CLUSTER_NAME,
                    region=REGION,
                    cluster_config_dict={
                        "softwareConfig": {
                            "properties": {
                                # Create a single-node cluster
                                # This needs to be the string "true" when
                                # serialized, not a boolean true
                                "dataproc:dataproc.allow.zero.workers": "true"
                            }
                        }
                    },
                )
            },
        )
        assert result.success


def test_wait_for_job_with_timeout_pydantic():
    """Test submitting a job with timeout of 0 second so that it always fails."""
    with mock.patch("httplib2.Http", new=HttpSnooper):

        @job
        def test_dataproc():
            configurable_dataproc_op()

        try:
            test_dataproc.execute_in_process(
                run_config=RunConfig(
                    ops={
                        "configurable_dataproc_op": DataprocOpConfig(
                            job_scoped_cluster=True,
                            project_id=PROJECT_ID,
                            region=REGION,
                            job_timeout_in_seconds=0,
                            job_config={
                                "reference": {"projectId": PROJECT_ID},
                                "placement": {"clusterName": CLUSTER_NAME},
                                "hiveJob": {"queryList": {"queries": ["SHOW DATABASES"]}},
                            },
                        )
                    },
                ),
                resources={
                    "dataproc": DataprocResource(
                        project_id=PROJECT_ID,
                        cluster_name=CLUSTER_NAME,
                        region=REGION,
                        cluster_config_dict={
                            "softwareConfig": {
                                "properties": {
                                    # Create a single-node cluster
                                    # This needs to be the string "true" when
                                    # serialized, not a boolean true
                                    "dataproc:dataproc.allow.zero.workers": "true"
                                }
                            }
                        },
                    )
                },
            )
            assert False
        except Exception as e:
            assert "Job run timed out" in str(e)
