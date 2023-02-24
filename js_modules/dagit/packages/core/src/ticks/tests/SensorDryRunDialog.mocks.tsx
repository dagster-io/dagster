import {MockedResponse} from '@apollo/client/testing';

import {InstigationStatus, RunRequest} from '../../graphql/types';
import {SET_CURSOR_MUTATION} from '../../sensors/EditCursorDialog';
import {SetSensorCursorMutation} from '../../sensors/types/EditCursorDialog.types';
import {EVALUATE_SENSOR_MUTATION} from '../SensorDryRunDialog';
import {SensorDryRunMutation} from '../types/SensorDryRunDialog.types';

export const runRequests: RunRequest[] = [
  {
    runConfigYaml:
      'solids:\n  read_file:\n    config:\n      directory: /Users/marcosalazar/code/dagster/js_modules/dagit/packages/core/src/ticks/tests\n      filename: SensorDryRun.mocks.tsx\n',
    tags: [
      {
        key: 'dagster1',
        value: 'test1',
        __typename: 'PipelineTag',
      },
      {
        key: 'marco2',
        value: 'salazar2',
        __typename: 'PipelineTag',
      },
    ],
    runKey: 'SensorDryRun.mocks.tsx:1675723096.8630984',
    __typename: 'RunRequest',
  },
  {
    runConfigYaml:
      'solids:\n  read_file:\n    config:\n      directory: /Users/marcosalazar/code/dagster/js_modules/dagit/packages/core/src/ticks/tests\n      filename: SensorDryRun.test.tsx\n',
    tags: [
      {
        key: 'dagster3',
        value: 'test3',
        __typename: 'PipelineTag',
      },
      {
        key: 'marco4',
        value: 'salazar4',
        __typename: 'PipelineTag',
      },
    ],
    runKey: 'SensorDryRun.test.tsx:1675722402.9114182',
    __typename: 'RunRequest',
  },
  {
    runConfigYaml:
      'solids:\n  read_file:\n    config:\n      directory: /Users/marcosalazar/code/dagster/js_modules/dagit/packages/core/src/ticks/tests\n      filename: DryRunRequestTable.test.tsx\n',
    tags: [
      {
        key: 'dagster6',
        value: 'test',
        __typename: 'PipelineTag',
      },
      {
        key: 'marco6',
        value: 'salazar',
        __typename: 'PipelineTag',
      },
    ],
    runKey: 'DryRunRequestTable.test.tsx:1675705668.9931223',
    __typename: 'RunRequest',
  },
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
      __typename: 'DagitMutation',
      sensorDryRun: {
        __typename: 'DryRunInstigationTick',
        timestamp: null,
        evaluationResult: {
          cursor: 'a new cursor',
          runRequests,
          skipReason: null,
          error: null,
          __typename: 'TickEvaluation',
        },
      },
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
      __typename: 'DagitMutation',
      sensorDryRun: {
        __typename: 'DryRunInstigationTick',
        timestamp: null,
        evaluationResult: {
          cursor: null,
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
      __typename: 'DagitMutation',
      sensorDryRun: {
        __typename: 'DryRunInstigationTick',
        timestamp: null,
        evaluationResult: {
          cursor: '',
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
      __typename: 'DagitMutation',
      setSensorCursor: {
        __typename: 'Sensor',
        id: '8c8110e095e45239948246b18f9c66def47a2a11',
        sensorState: {
          id: 'abe2076b4d21ada25109611e1d8222ed6954f618',
          status: InstigationStatus.RUNNING,
          typeSpecificData: {
            lastCursor: '',
            __typename: 'SensorData',
          },
          __typename: 'InstigationState',
        },
      },
    },
  },
};
