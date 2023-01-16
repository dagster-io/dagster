from typing import NamedTuple, Optional

from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.execution.retries import RetryMode
from dagster._core.instance import DagsterInstance
from dagster._serdes.serdes import (
    deserialize_as,
    serialize_dagster_namedtuple,
    whitelist_for_serdes,
)


@whitelist_for_serdes
class RemoteStepInformation(NamedTuple):
    retry_mode: Optional[RetryMode]
    known_state: Optional[KnownExecutionState]


def get_kv_key_for_step_args(run_id: str, step_key: str) -> str:
    return f"STEPARGS:{run_id}:{step_key}"


def set_remote_step_info(
    instance: DagsterInstance, run_id: str, step_key: str, remote_step_info: RemoteStepInformation
):
    step_args_kv_key = get_kv_key_for_step_args(run_id, step_key)
    return instance.kvs_set(
        {
            step_args_kv_key: serialize_dagster_namedtuple(remote_step_info),
        }
    )


def get_remote_step_info(
    instance: DagsterInstance, run_id: str, step_key: str
) -> RemoteStepInformation:
    kv_key = get_kv_key_for_step_args(run_id, step_key)
    remote_step_info_json = instance.kvs_get({kv_key})[kv_key]
    return deserialize_as(remote_step_info_json, RemoteStepInformation)
