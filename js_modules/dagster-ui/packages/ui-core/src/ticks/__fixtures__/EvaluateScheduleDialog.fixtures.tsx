import {MockedResponse} from '@apollo/client/testing';

import {
  RunStatus,
  buildDryRunInstigationTick,
  buildErrorChainLink,
  buildLaunchMultipleRunsResult,
  buildLaunchRunSuccess,
  buildPipelineSnapshot,
  buildPipelineTag,
  buildPythonError,
  buildRun,
  buildRunRequest,
  buildSchedule,
  buildTickEvaluation,
} from '../../graphql/types';
import {LAUNCH_MULTIPLE_RUNS_MUTATION} from '../../runs/RunUtils';
import {LaunchMultipleRunsMutation} from '../../runs/types/RunUtils.types';
import {GET_SCHEDULE_QUERY, SCHEDULE_DRY_RUN_MUTATION} from '../EvaluateScheduleDialog';
import {GetScheduleQuery, ScheduleDryRunMutation} from '../types/EvaluateScheduleDialog.types';

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
      __typename: 'Query',
      scheduleOrError: buildSchedule({
        id: 'foo',
        name: 'configurable_job_schedule',
        potentialTickTimestamps: [1, 2, 4, 5, 6, 7, 8, 9, 10],
      }),
    },
  },
};

export const scheduleDryWithWithRunRequest = {
  __typename: 'Mutation' as const,
  scheduleDryRun: buildDryRunInstigationTick({
    timestamp: 1674950400,
    evaluationResult: buildTickEvaluation({
      runRequests: [
        buildRunRequest({
          runConfigYaml:
            'ops:\n  configurable_op:\n    config:\n      scheduled_date: 2023-01-29\n',
          tags: [
            buildPipelineTag({
              key: 'dagster/schedule_name',
              value: 'configurable_job_schedule',
            }),
            buildPipelineTag({
              key: 'date',
              value: '2023-01-29',
              __typename: 'PipelineTag' as const,
            }),
            buildPipelineTag({
              key: 'github_test',
              value: 'test',
            }),
            buildPipelineTag({
              key: 'okay_t2',
              value: 'okay',
            }),
          ],
          runKey: 'EvaluateScheduleDialog.test.tsx:1675705668.993122345',
        }),
      ],
      skipReason: null,
      error: null,
    }),
  }),
};

export const scheduleDryWithWithRunRequestUndefinedName = {
  __typename: 'Mutation' as const,
  scheduleDryRun: buildDryRunInstigationTick({
    timestamp: 1674950400,
    evaluationResult: buildTickEvaluation({
      runRequests: [
        buildRunRequest({
          jobName: undefined,
          runConfigYaml:
            'ops:\n  configurable_op:\n    config:\n      scheduled_date: 2023-01-29\n',
          tags: [
            buildPipelineTag({
              key: 'dagster/schedule_name',
              value: 'configurable_job_schedule',
            }),
            buildPipelineTag({
              key: 'date',
              value: '2023-01-29',
              __typename: 'PipelineTag' as const,
            }),
            buildPipelineTag({
              key: 'github_test',
              value: 'test',
            }),
            buildPipelineTag({
              key: 'okay_t2',
              value: 'okay',
            }),
          ],
          runKey: 'EvaluateScheduleDialog.test.tsx:1675705668.993122345',
        }),
      ],
      skipReason: null,
      error: null,
    }),
  }),
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

export const ScheduleDryRunMutationRunRequestsWithUndefinedName: MockedResponse<ScheduleDryRunMutation> =
  {
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
    result: {data: scheduleDryWithWithRunRequestUndefinedName},
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
      __typename: 'Mutation',
      scheduleDryRun: buildDryRunInstigationTick({
        timestamp: null,
        evaluationResult: buildTickEvaluation({
          runRequests: null,
          skipReason: null,
          error: buildPythonError({
            message:
              'dagster._core.errors.SensorExecutionError: Error occurred during the execution of evaluation_fn for sensor toy_file_sensor\n',
            stack: [
              '  File "/Users/marcosalazar/code/dagster/python_modules/dagster/dagster/_grpc/impl.py", line 328, in get_external_sensor_execution\n    return sensor_def.evaluate_tick(sensor_context)\n',
              '  File "/Users/marcosalazar/.pyenv/versions/3.9.9/lib/python3.9/contextlib.py", line 137, in __exit__\n    self.gen.throw(typ, value, traceback)\n',
              '  File "/Users/marcosalazar/code/dagster/python_modules/dagster/dagster/_core/errors.py", line 213, in user_code_error_boundary\n    raise error_cls(\n',
            ],
            errorChain: [
              buildErrorChainLink({
                isExplicitLink: true,
                error: buildPythonError({
                  message: 'Exception: testing\n',
                  stack: [
                    '  File "/Users/marcosalazar/code/dagster/python_modules/dagster/dagster/_core/errors.py", line 206, in user_code_error_boundary\n    yield\n',
                    '  File "/Users/marcosalazar/code/dagster/python_modules/dagster/dagster/_grpc/impl.py", line 328, in get_external_sensor_execution\n    return sensor_def.evaluate_tick(sensor_context)\n',
                    '  File "/Users/marcosalazar/code/dagster/python_modules/dagster/dagster/_core/definitions/sensor_definition.py", line 428, in evaluate_tick\n    result = list(self._evaluation_fn(context))\n',
                    '  File "/Users/marcosalazar/code/dagster/python_modules/dagster/dagster/_core/definitions/sensor_definition.py", line 598, in _wrapped_fn\n    for item in result:\n',
                    '  File "/Users/marcosalazar/code/dagster/python_modules/dagster-test/dagster_test/toys/sensors.py", line 76, in toy_file_sensor\n',
                  ],
                }),
              }),
            ],
          }),
        }),
      }),
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
      __typename: 'Mutation',
      scheduleDryRun: buildDryRunInstigationTick({
        timestamp: null,
        evaluationResult: buildTickEvaluation({
          runRequests: [],
          skipReason:
            'No directory specified at environment variable `DAGSTER_TOY_SENSOR_DIRECTORY`',
          error: null,
        }),
      }),
    },
  },
};

export const ScheduleLaunchAllMutation: MockedResponse<LaunchMultipleRunsMutation> = {
  request: {
    query: LAUNCH_MULTIPLE_RUNS_MUTATION,
    variables: {
      executionParamsList: [
        {
          runConfigData: 'ops:\n  configurable_op:\n    config:\n      scheduled_date: 2023-01-29',
          selector: {
            jobName: 'saepe',
            repositoryLocationName: 'testLocation',
            repositoryName: 'testName',
            assetSelection: [],
            assetCheckSelection: [],
            solidSelection: undefined,
          },
          mode: 'default',
          executionMetadata: {
            tags: [
              {
                key: 'dagster/schedule_name',
                value: 'configurable_job_schedule',
              },
              {
                key: 'date',
                value: '2023-01-29',
              },
              {
                key: 'github_test',
                value: 'test',
              },
              {
                key: 'okay_t2',
                value: 'okay',
              },
            ],
          },
        },
      ],
    },
  },
  result: {
    data: {
      __typename: 'Mutation',
      launchMultipleRuns: buildLaunchMultipleRunsResult({
        launchMultipleRunsResult: [
          buildLaunchRunSuccess({
            run: buildRun({
              id: '504b3a77-d6c4-440c-a128-7f59c9d75d59',
              pipeline: buildPipelineSnapshot({
                name: 'saepe',
              }),
              tags: [
                buildPipelineTag({
                  key: 'dagster/schedule_name',
                  value: 'configurable_job_schedule',
                }),
                buildPipelineTag({
                  key: 'date',
                  value: '2023-01-29',
                }),
                buildPipelineTag({
                  key: 'github_test',
                  value: 'test',
                }),
                buildPipelineTag({
                  key: 'okay_t2',
                  value: 'okay',
                }),
              ],
              status: RunStatus.QUEUED,
              runConfigYaml:
                'ops:\n  configurable_op:\n    config:\n      scheduled_date: 2023-01-29',
              mode: 'default',
              resolvedOpSelection: null,
            }),
          }),
        ],
      }),
    },
  },
};

export const ScheduleLaunchAllMutationWithUndefinedName: MockedResponse<LaunchMultipleRunsMutation> =
  {
    request: {
      query: LAUNCH_MULTIPLE_RUNS_MUTATION,
      variables: {
        executionParamsList: [
          {
            runConfigData:
              'ops:\n  configurable_op:\n    config:\n      scheduled_date: 2023-01-29',
            selector: {
              jobName: 'testJobName', // fallback
              repositoryLocationName: 'testLocation',
              repositoryName: 'testName',
              assetSelection: [],
              assetCheckSelection: [],
              solidSelection: undefined,
            },
            mode: 'default',
            executionMetadata: {
              tags: [
                {
                  key: 'dagster/schedule_name',
                  value: 'configurable_job_schedule',
                },
                {
                  key: 'date',
                  value: '2023-01-29',
                },
                {
                  key: 'github_test',
                  value: 'test',
                },
                {
                  key: 'okay_t2',
                  value: 'okay',
                },
              ],
            },
          },
        ],
      },
    },
    result: {
      data: {
        __typename: 'Mutation',
        launchMultipleRuns: buildLaunchMultipleRunsResult({
          launchMultipleRunsResult: [
            buildLaunchRunSuccess({
              run: buildRun({
                id: '504b3a77-d6c4-440c-a128-7f59c9d75d59',
                pipeline: buildPipelineSnapshot({
                  name: 'testJobName', // fallback
                }),
                tags: [
                  buildPipelineTag({
                    key: 'dagster/schedule_name',
                    value: 'configurable_job_schedule',
                  }),
                  buildPipelineTag({
                    key: 'date',
                    value: '2023-01-29',
                  }),
                  buildPipelineTag({
                    key: 'github_test',
                    value: 'test',
                  }),
                  buildPipelineTag({
                    key: 'okay_t2',
                    value: 'okay',
                  }),
                ],
                status: RunStatus.QUEUED,
                runConfigYaml:
                  'ops:\n  configurable_op:\n    config:\n      scheduled_date: 2023-01-29',
                mode: 'default',
                resolvedOpSelection: null,
              }),
            }),
          ],
        }),
      },
    },
  };
