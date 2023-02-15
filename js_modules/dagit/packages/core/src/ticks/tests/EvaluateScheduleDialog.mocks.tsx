import {MockedResponse} from '@apollo/client/testing';

import {GET_SCHEDULE_QUERY, SCHEDULE_DRY_RUN_MUTATION} from '../EvaluateScheduleDialog';
import {GetScheduleQuery, ScheduleDryRunMutation} from '../types/EvaluateSchedule.types';

export const GetScheduleQueryMock: MockedResponse<GetScheduleQuery> = {
  request: {
    query: GET_SCHEDULE_QUERY,
    variables: {
      scheduleSelector: {
        scheduleName: 'test',
        repositoryLocationName: 'testLocation',
        repositoryName: 'testName',
      },
    },
  },
  result: {
    data: {
      __typename: 'DagitQuery',
      scheduleOrError: {
        __typename: 'Schedule',
        name: 'configurable_job_schedule',
        potentialTickTimestamps: [1, 2, 4, 5, 6, 7, 8, 9, 10],
      },
    },
  },
};

export const scheduleDryWithWithRunRequest = {
  __typename: 'DagitMutation' as const,
  scheduleDryRun: {
    __typename: 'DryRunInstigationTick' as const,
    timestamp: 1674950400,
    evaluationResult: {
      runRequests: [
        {
          runConfigYaml:
            'ops:\n  configurable_op:\n    config:\n      scheduled_date: 2023-01-29\n',
          tags: [
            {
              key: 'dagster/schedule_name',
              value: 'configurable_job_schedule',
              __typename: 'PipelineTag' as const,
            },
            {
              key: 'date',
              value: '2023-01-29',
              __typename: 'PipelineTag' as const,
            },
            {
              key: 'github_test',
              value: 'test',
              __typename: 'PipelineTag' as const,
            },
            {
              key: 'okay_t2',
              value: 'okay',
              __typename: 'PipelineTag' as const,
            },
          ],
          runKey: null,
          __typename: 'RunRequest' as const,
        },
      ],
      skipReason: null,
      error: null,
      __typename: 'TickEvaluation' as const,
    },
  },
};

export const ScheduleDryRunMutationRunRequests: MockedResponse<ScheduleDryRunMutation> = {
  request: {
    query: SCHEDULE_DRY_RUN_MUTATION,
    variables: {
      selectorData: {
        scheduleName: 'test',
        repositoryLocationName: 'testLocation',
        repositoryName: 'testName',
      },
      timestamp: 5,
    },
  },
  result: {data: scheduleDryWithWithRunRequest},
};

export const ScheduleDryRunMutationError: MockedResponse<ScheduleDryRunMutation> = {
  request: {
    query: SCHEDULE_DRY_RUN_MUTATION,
    variables: {
      selectorData: {
        scheduleName: 'test',
        repositoryLocationName: 'testLocation',
        repositoryName: 'testName',
      },
      timestamp: 5,
    },
  },
  result: {
    data: {
      __typename: 'DagitMutation',
      scheduleDryRun: {
        __typename: 'DryRunInstigationTick',
        timestamp: null,
        evaluationResult: {
          runRequests: null,
          skipReason: null,
          error: {
            __typename: 'PythonError',
            message:
              'dagster._core.errors.SensorExecutionError: Error occurred during the execution of evaluation_fn for sensor toy_file_sensor\n',
            stack: [
              '  File "/Users/marcosalazar/code/dagster/python_modules/dagster/dagster/_grpc/impl.py", line 328, in get_external_sensor_execution\n    return sensor_def.evaluate_tick(sensor_context)\n',
              '  File "/Users/marcosalazar/.pyenv/versions/3.9.9/lib/python3.9/contextlib.py", line 137, in __exit__\n    self.gen.throw(typ, value, traceback)\n',
              '  File "/Users/marcosalazar/code/dagster/python_modules/dagster/dagster/_core/errors.py", line 213, in user_code_error_boundary\n    raise error_cls(\n',
            ],
            errorChain: [
              {
                isExplicitLink: true,
                error: {
                  message: 'Exception: testing\n',
                  stack: [
                    '  File "/Users/marcosalazar/code/dagster/python_modules/dagster/dagster/_core/errors.py", line 206, in user_code_error_boundary\n    yield\n',
                    '  File "/Users/marcosalazar/code/dagster/python_modules/dagster/dagster/_grpc/impl.py", line 328, in get_external_sensor_execution\n    return sensor_def.evaluate_tick(sensor_context)\n',
                    '  File "/Users/marcosalazar/code/dagster/python_modules/dagster/dagster/_core/definitions/sensor_definition.py", line 428, in evaluate_tick\n    result = list(self._evaluation_fn(context))\n',
                    '  File "/Users/marcosalazar/code/dagster/python_modules/dagster/dagster/_core/definitions/sensor_definition.py", line 598, in _wrapped_fn\n    for item in result:\n',
                    '  File "/Users/marcosalazar/code/dagster/python_modules/dagster-test/dagster_test/toys/sensors.py", line 76, in toy_file_sensor\n',
                  ],
                  __typename: 'PythonError',
                },
                __typename: 'ErrorChainLink',
              },
            ],
          },
          __typename: 'TickEvaluation',
        },
      },
    },
  },
};

export const ScheduleDryRunMutationSkipped: MockedResponse<ScheduleDryRunMutation> = {
  request: {
    query: SCHEDULE_DRY_RUN_MUTATION,
    variables: {
      selectorData: {
        scheduleName: 'test',
        repositoryLocationName: 'testLocation',
        repositoryName: 'testName',
      },
      timestamp: 5,
    },
  },
  result: {
    data: {
      __typename: 'DagitMutation',
      scheduleDryRun: {
        __typename: 'DryRunInstigationTick',
        timestamp: null,
        evaluationResult: {
          runRequests: [],
          skipReason:
            'No directory specified at environment variable `DAGSTER_TOY_SENSOR_DIRECTORY`',
          error: null,
          __typename: 'TickEvaluation',
        },
      },
    },
  },
};
