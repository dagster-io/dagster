import sys
from collections import namedtuple

from dagster import check
from dagster.core.host_representation import PipelineSelector
from dagster.utils.error import serializable_error_info_from_exc_info


def capture_error(fn):
    def _fn(*args, **kwargs):
        from dagster_graphql.schema.errors import GraphenePythonError

        try:
            return fn(*args, **kwargs)
        except UserFacingGraphQLError as de_exception:
            return de_exception.error
        except Exception:  # pylint: disable=broad-except
            return GraphenePythonError(serializable_error_info_from_exc_info(sys.exc_info()))

    return _fn


class UserFacingGraphQLError(Exception):
    def __init__(self, error):
        self.error = error
        message = "[{cls}] {message}".format(
            cls=error.__class__.__name__,
            message=error.message if hasattr(error, "message") else None,
        )
        super(UserFacingGraphQLError, self).__init__(message)


def pipeline_selector_from_graphql(context, data):
    from dagster_graphql.implementation.context import RequestContext

    check.inst_param(context, "context", RequestContext)

    return PipelineSelector(
        location_name=data["repositoryLocationName"],
        repository_name=data["repositoryName"],
        pipeline_name=data["pipelineName"],
        solid_selection=data.get("solidSelection"),
    )


class ExecutionParams(
    namedtuple(
        "_ExecutionParams",
        "selector run_config mode execution_metadata step_keys",
    )
):
    def __new__(cls, selector, run_config, mode, execution_metadata, step_keys):
        check.dict_param(run_config, "run_config", key_type=str)
        check.opt_list_param(step_keys, "step_keys", of_type=str)

        return super(ExecutionParams, cls).__new__(
            cls,
            selector=check.inst_param(selector, "selector", PipelineSelector),
            run_config=run_config,
            mode=check.str_param(mode, "mode"),
            execution_metadata=check.inst_param(
                execution_metadata, "execution_metadata", ExecutionMetadata
            ),
            step_keys=step_keys,
        )

    def to_graphql_input(self):
        return {
            "selector": self.selector.to_graphql_input(),
            "runConfigData": self.run_config,
            "mode": self.mode,
            "executionMetadata": self.execution_metadata.to_graphql_input(),
            "stepKeys": self.step_keys,
        }


class ExecutionMetadata(namedtuple("_ExecutionMetadata", "run_id tags root_run_id parent_run_id")):
    def __new__(cls, run_id, tags, root_run_id=None, parent_run_id=None):
        return super(ExecutionMetadata, cls).__new__(
            cls,
            check.opt_str_param(run_id, "run_id"),
            check.dict_param(tags, "tags", key_type=str, value_type=str),
            check.opt_str_param(root_run_id, "root_run_id"),
            check.opt_str_param(parent_run_id, "parent_run_id"),
        )

    def to_graphql_input(self):
        return {
            "runId": self.run_id,
            "tags": [{"key": k, "value": v} for k, v in self.tags.items()],
            "rootRunId": self.root_run_id,
            "parentRunId": self.parent_run_id,
        }
