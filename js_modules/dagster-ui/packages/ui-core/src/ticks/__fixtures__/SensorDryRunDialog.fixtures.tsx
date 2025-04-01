import {MockedResponse} from '@apollo/client/testing';

import {
  InstigationStatus,
  RunRequest,
  RunStatus,
  buildDryRunInstigationTick,
  buildErrorChainLink,
  buildInstigationState,
  buildLaunchMultipleRunsResult,
  buildLaunchRunSuccess,
  buildPipelineSnapshot,
  buildPipelineTag,
  buildPythonError,
  buildRun,
  buildRunRequest,
  buildSensor,
  buildSensorData,
  buildTickEvaluation,
} from '../../graphql/types';
import {LAUNCH_MULTIPLE_RUNS_MUTATION} from '../../runs/RunUtils';
import {LaunchMultipleRunsMutation} from '../../runs/types/RunUtils.types';
import {SET_CURSOR_MUTATION} from '../../sensors/EditCursorDialog';
import {SetSensorCursorMutation} from '../../sensors/types/EditCursorDialog.types';
import {EVALUATE_SENSOR_MUTATION} from '../SensorDryRunDialog';
import {SensorDryRunMutation} from '../types/SensorDryRunDialog.types';

export const runRequests: RunRequest[] = [
  buildRunRequest({
    runKey: 'DryRunRequestTable.test.tsx:1675705668.9931223',
    runConfigYaml:
      'solids:\n  read_file:\n    config:\n      directory: /Users/marcosalazar/code/dagster/js_modules/dagster-ui/packages/ui-core/src/ticks/tests\n      filename: DryRunRequestTable.test.tsx\n',
    tags: [
      buildPipelineTag({key: 'dagster2', value: 'test'}),
      buildPipelineTag({key: 'marco2', value: 'salazar2'}),
    ],
  }),
  buildRunRequest({
    runKey: 'DryRunRequestTable.test.tsx:1675705668.993122345',
    runConfigYaml:
      'solids:\n  read_file:\n    config:\n      directory: /Users/marcosalazar/code/dagster/js_modules/dagster-ui/packages/ui-core/src/ticks/tests\n      filename: DryRunRequestTable.test.tsx\n',
    tags: [
      buildPipelineTag({key: 'dagster3', value: 'test'}),
      buildPipelineTag({key: 'marco3', value: 'salazar3'}),
    ],
  }),
  buildRunRequest({
    runKey: 'DryRunRequestTable.test.tsx:1675705668.993122367',
    runConfigYaml:
      'solids:\n  read_file:\n    config:\n      directory: /Users/marcosalazar/code/dagster/js_modules/dagster-ui/packages/ui-core/src/ticks/tests\n      filename: DryRunRequestTable.test.tsx\n',
    tags: [
      buildPipelineTag({key: 'dagster6', value: 'test'}),
      buildPipelineTag({key: 'marco6', value: 'salazar6'}),
    ],
  }),
];

export const runRequestWithUndefinedJobName: RunRequest[] = [
  buildRunRequest({
    jobName: undefined, // undefined jobName
    runKey: 'DryRunRequestTable.test.tsx:1675705668.9931223',
    runConfigYaml:
      'solids:\n  read_file:\n    config:\n      directory: /Users/marcosalazar/code/dagster/js_modules/dagster-ui/packages/ui-core/src/ticks/tests\n      filename: DryRunRequestTable.test.tsx\n',
    tags: [
      buildPipelineTag({key: 'dagster2', value: 'test'}),
      buildPipelineTag({key: 'marco2', value: 'salazar2'}),
    ],
  }),
];

export const SensorDryRunMutationRunRequests: MockedResponse<SensorDryRunMutation> = {
  request: {
    query: EVALUATE_SENSOR_MUTATION,
    variables: {
      selectorData: {
        sensorName: 'test',
        repositoryLocationName: 'testLocation',
        repositoryName: 'testName',
      },
      cursor: 'testCursortesting123',
    },
  },
  result: {
    data: {
      __typename: 'Mutation',
      sensorDryRun: buildDryRunInstigationTick({
        evaluationResult: buildTickEvaluation({
          cursor: 'a new cursor',
          runRequests,
          error: null,
        }),
      }),
    },
  },
};

export const SensorDryRunMutationRunRequestWithUndefinedJobName: MockedResponse<SensorDryRunMutation> =
  {
    request: {
      query: EVALUATE_SENSOR_MUTATION,
      variables: {
        selectorData: {
          sensorName: 'test',
          repositoryLocationName: 'testLocation',
          repositoryName: 'testName',
        },
        cursor: 'testCursortesting123',
      },
    },
    result: {
      data: {
        __typename: 'Mutation',
        sensorDryRun: buildDryRunInstigationTick({
          evaluationResult: buildTickEvaluation({
            cursor: 'a new cursor',
            runRequests: runRequestWithUndefinedJobName,
            error: null,
          }),
        }),
      },
    },
  };

export const SensorDryRunMutationError: MockedResponse<SensorDryRunMutation> = {
  request: {
    query: EVALUATE_SENSOR_MUTATION,
    variables: {
      selectorData: {
        sensorName: 'test',
        repositoryLocationName: 'testLocation',
        repositoryName: 'testName',
      },
      cursor: 'testCursortesting123',
    },
  },
  result: {
    data: {
      __typename: 'Mutation',
      sensorDryRun: buildDryRunInstigationTick({
        evaluationResult: buildTickEvaluation({
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

export const SensorDryRunMutationSkipped: MockedResponse<SensorDryRunMutation> = {
  request: {
    query: EVALUATE_SENSOR_MUTATION,
    variables: {
      selectorData: {
        sensorName: 'test',
        repositoryLocationName: 'testLocation',
        repositoryName: 'testName',
      },
      cursor: 'testCursortesting123',
    },
  },
  result: {
    data: {
      __typename: 'Mutation',
      sensorDryRun: buildDryRunInstigationTick({
        evaluationResult: buildTickEvaluation({
          cursor: '',
          runRequests: [],
          skipReason:
            'No directory specified at environment variable `DAGSTER_TOY_SENSOR_DIRECTORY`',
          error: null,
        }),
      }),
    },
  },
};

export const PersistCursorValueMock: MockedResponse<SetSensorCursorMutation> = {
  request: {
    query: SET_CURSOR_MUTATION,
    variables: {
      sensorSelector: {
        sensorName: 'test',
        repositoryLocationName: 'testLocation',
        repositoryName: 'testName',
      },
      cursor: 'a new cursor',
    },
  },
  result: {
    data: {
      __typename: 'Mutation',
      setSensorCursor: buildSensor({
        id: '8c8110e095e45239948246b18f9c66def47a2a11',
        sensorState: buildInstigationState({
          id: 'abe2076b4d21ada25109611e1d8222ed6954f618',
          status: InstigationStatus.RUNNING,
          typeSpecificData: buildSensorData({
            lastCursor: '',
          }),
        }),
      }),
    },
  },
};

export const SensorLaunchAllMutation: MockedResponse<LaunchMultipleRunsMutation> = {
  request: {
    query: LAUNCH_MULTIPLE_RUNS_MUTATION,
    variables: {
      executionParamsList: [
        {
          runConfigData:
            'solids:\n  read_file:\n    config:\n      directory: /Users/marcosalazar/code/dagster/js_modules/dagster-ui/packages/ui-core/src/ticks/tests\n      filename: DryRunRequestTable.test.tsx',
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
                key: 'dagster2',
                value: 'test',
              },
              {
                key: 'marco2',
                value: 'salazar2',
              },
            ],
          },
        },
        {
          runConfigData:
            'solids:\n  read_file:\n    config:\n      directory: /Users/marcosalazar/code/dagster/js_modules/dagster-ui/packages/ui-core/src/ticks/tests\n      filename: DryRunRequestTable.test.tsx',
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
                key: 'dagster3',
                value: 'test',
              },
              {
                key: 'marco3',
                value: 'salazar3',
              },
            ],
          },
        },
        {
          runConfigData:
            'solids:\n  read_file:\n    config:\n      directory: /Users/marcosalazar/code/dagster/js_modules/dagster-ui/packages/ui-core/src/ticks/tests\n      filename: DryRunRequestTable.test.tsx',
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
                key: 'dagster6',
                value: 'test',
              },
              {
                key: 'marco6',
                value: 'salazar6',
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
            __typename: 'LaunchRunSuccess',
            run: buildRun({
              __typename: 'Run',
              id: '504b3a77-d6c4-440c-a128-7f59c9d75d59',
              pipeline: buildPipelineSnapshot({
                name: 'saepe',
              }),
              tags: [
                buildPipelineTag({key: 'dagster2', value: 'test'}),
                buildPipelineTag({key: 'marco2', value: 'salazar2'}),
              ],
              status: RunStatus.QUEUED,
              runConfigYaml:
                'solids:\n  read_file:\n    config:\n      directory: /Users/marcosalazar/code/dagster/js_modules/dagster-ui/packages/ui-core/src/ticks/tests\n      filename: DryRunRequestTable.test.tsx\n',
              mode: 'default',
              resolvedOpSelection: null,
            }),
          }),
          buildLaunchRunSuccess({
            __typename: 'LaunchRunSuccess',
            run: buildRun({
              __typename: 'Run',
              id: '6745cd03-3d89-4fd2-a41f-6b9d9ffdc134',
              pipeline: buildPipelineSnapshot({
                name: 'saepe',
              }),
              tags: [
                buildPipelineTag({key: 'dagster3', value: 'test'}),
                buildPipelineTag({key: 'marco3', value: 'salazar3'}),
              ],

              status: RunStatus.QUEUED,
              runConfigYaml:
                'solids:\n  read_file:\n    config:\n      directory: /Users/marcosalazar/code/dagster/js_modules/dagster-ui/packages/ui-core/src/ticks/tests\n      filename: DryRunRequestTable.test.tsx\n',
              mode: 'default',
              resolvedOpSelection: null,
            }),
          }),
          buildLaunchRunSuccess({
            run: buildRun({
              id: '7ed35f69-42cf-4518-84a4-c97d0551a56b',
              pipeline: buildPipelineSnapshot({
                name: 'simple_config_job',
              }),
              tags: [
                buildPipelineTag({key: 'dagster6', value: 'test'}),
                buildPipelineTag({key: 'marco6', value: 'salazar6'}),
              ],
              status: RunStatus.QUEUED,
              runConfigYaml:
                'solids:\n  read_file:\n    config:\n      directory: /Users/marcosalazar/code/dagster/js_modules/dagster-ui/packages/ui-core/src/ticks/tests\n      filename: DryRunRequestTable.test.tsx\n',

              mode: 'default',
              resolvedOpSelection: null,
            }),
          }),
        ],
      }),
    },
  },
};

export const SensorLaunchAllMutation1JobWithUndefinedJobName: MockedResponse<LaunchMultipleRunsMutation> =
  {
    request: {
      query: LAUNCH_MULTIPLE_RUNS_MUTATION,
      variables: {
        executionParamsList: [
          {
            runConfigData:
              'solids:\n  read_file:\n    config:\n      directory: /Users/marcosalazar/code/dagster/js_modules/dagster-ui/packages/ui-core/src/ticks/tests\n      filename: DryRunRequestTable.test.tsx',
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
                  key: 'dagster2',
                  value: 'test',
                },
                {
                  key: 'marco2',
                  value: 'salazar2',
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
              __typename: 'LaunchRunSuccess',
              run: buildRun({
                __typename: 'Run',
                id: '504b3a77-d6c4-440c-a128-7f59c9d75d59',
                pipeline: buildPipelineSnapshot({
                  name: 'testJobName',
                }),
                tags: [
                  buildPipelineTag({key: 'dagster2', value: 'test'}),
                  buildPipelineTag({key: 'marco2', value: 'salazar2'}),
                ],
                status: RunStatus.QUEUED,
                runConfigYaml:
                  'solids:\n  read_file:\n    config:\n      directory: /Users/marcosalazar/code/dagster/js_modules/dagster-ui/packages/ui-core/src/ticks/tests\n      filename: DryRunRequestTable.test.tsx\n',
                mode: 'default',
                resolvedOpSelection: null,
              }),
            }),
          ],
        }),
      },
    },
  };
