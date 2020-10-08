from future.standard_library import install_aliases  # isort:skip

install_aliases()  # isort:skip

import weakref

import requests
from dagster_graphql.client.query import EXECUTE_RUN_IN_PROCESS_MUTATION
from requests import RequestException

from dagster import Bool, Field, check, seven
from dagster.core.errors import DagsterLaunchFailedError
from dagster.core.host_representation import ExternalPipeline
from dagster.core.launcher import RunLauncher
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.serdes import ConfigurableClass, ConfigurableClassData
from dagster.seven import urljoin, urlparse


class RemoteDagitRunLauncher(RunLauncher, ConfigurableClass):
    def __init__(self, address, timeout, inst_data=None):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self._address = check.str_param(address, "address")
        self._timeout = check.numeric_param(timeout, "timeout")
        self._handle = None
        self._instance_ref = None
        self._validated = False

        parsed_url = urlparse(address)
        check.invariant(
            parsed_url.scheme and parsed_url.netloc,
            "Address {address} is not a valid URL. Host URL should include scheme ie http://localhost".format(
                address=self._address
            ),
        )

    @classmethod
    def config_type(cls):
        return {
            "address": str,
            "timeout": Field(float, is_required=False, default_value=30.0),
        }

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(
            address=config_value["address"], timeout=config_value["timeout"], inst_data=inst_data,
        )

    @property
    def inst_data(self):
        return self._inst_data

    @property
    def _instance(self):
        return self._instance_ref() if self._instance_ref else None

    def start(self, handle):
        self._handle = handle

    def stop(self):
        self._handle = None

    def validate(self):
        if self._validated:
            return
        try:
            sanity_check = requests.get(
                urljoin(self._address, "/dagit_info"), timeout=self._timeout
            )
            self._validated = sanity_check.status_code = 200 and "dagit" in sanity_check.text
        except RequestException:
            self._validated = False

        if not self._validated:
            raise DagsterLaunchFailedError(
                "Host {host} failed sanity check. It is not a dagit server.".format(
                    host=self._address
                ),
            )

    def initialize(self, instance):
        # Store a weakref to avoid a circular reference / enable GC
        self._instance_ref = weakref.ref(instance)

    def launch_run(self, instance, run, external_pipeline):
        check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)
        self.validate()

        variables = {
            "repositoryLocationName": external_pipeline.handle.location_name,
            "repositoryName": external_pipeline.handle.repository_name,
            "runId": run.run_id,
        }
        response = requests.post(
            urljoin(self._address, "/graphql"),
            params={
                "query": EXECUTE_RUN_IN_PROCESS_MUTATION,
                "variables": seven.json.dumps(variables),
            },
            timeout=self._timeout,
        )
        response.raise_for_status()
        result = response.json()["data"]["executeRunInProcess"]

        if result["__typename"] in ["LaunchPipelineRunSuccess", "PipelineConfigValidationInvalid"]:
            return self._instance.get_run_by_id(run.run_id)

        raise DagsterLaunchFailedError(
            "Failed to launch run with {cls} targeting {address}:\n{result}".format(
                cls=self.__class__.__name__, address=self._address, result=result
            )
        )

    def can_terminate(self, run_id):
        return False

    def terminate(self, run_id):
        check.not_implemented("Termination not supported")
