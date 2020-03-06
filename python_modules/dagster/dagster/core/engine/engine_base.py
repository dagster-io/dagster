import abc

import six

from dagster import check
from dagster.core.execution.retries import Retries


class Engine(six.with_metaclass(abc.ABCMeta)):  # pylint: disable=no-init
    @staticmethod
    @abc.abstractmethod
    def execute(pipeline_context, execution_plan):
        '''Core execution method.

        Args:
            pipeline_context (SystemPipelineExecutionContext): The pipeline execution context.
            execution_plan (ExecutionPlan): The plan to execute.
        '''


# This is a clever/greasy approach that the "orchestrator" engines use to defer core execution
# to the in process engine. Should be replaced with more formal separate abstractions.
# https://github.com/dagster-io/dagster/issues/2239
def override_env_for_inner_executor(environment_config, retries, step_key, marker_to_close):
    check.dict_param(environment_config, 'environment_config')
    check.inst_param(retries, 'retries', Retries)
    check.str_param(step_key, 'step_key')
    check.str_param(marker_to_close, 'marker_to_close')

    return dict(
        environment_config,
        execution={  # here we overwrite the "execution" key to change to in_process
            'in_process': {
                'config': {
                    'retries': {
                        'deferred': {
                            'previous_attempts': {step_key: retries.get_attempt_count(step_key)}
                        }
                    },
                    'marker_to_close': marker_to_close,
                }
            }
        },
    )
