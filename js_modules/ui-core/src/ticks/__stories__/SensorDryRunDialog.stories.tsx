import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {MemoryRouter} from 'react-router-dom';

import {
  buildAssetKey,
  buildDryRunInstigationTick,
  buildPipelineTag,
  buildRunRequest,
  buildTickEvaluation,
} from '../../graphql/builders';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {EVALUATE_SENSOR_MUTATION, SensorDryRunDialog} from '../SensorDryRunDialog';
import {
  SensorDryRunMutation,
  SensorDryRunMutationVariables,
} from '../types/SensorDryRunDialog.types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Ticks/SensorDryRunDialog',
  component: SensorDryRunDialog,
};

const SENSOR_NAME = 'my_event_sensor';
const JOB_NAME = 'my_target_job';
const REPO_ADDRESS = {name: 'my_repo', location: 'my_location'};
const CURRENT_CURSOR = '{"last_event_id": 42, "offset": "2024-01-15T00:00:00"}';

const buildSensorDryRunMock = (
  result: SensorDryRunMutation['sensorDryRun'],
): MockedResponse<SensorDryRunMutation, SensorDryRunMutationVariables> => ({
  request: {query: EVALUATE_SENSOR_MUTATION},
  variableMatcher: () => true,
  result: {
    data: {
      __typename: 'Mutation',
      sensorDryRun: result,
    },
  },
});

const withRunRequestsMock = buildSensorDryRunMock(
  buildDryRunInstigationTick({
    timestamp: Date.now() / 1000,
    evaluationResult: buildTickEvaluation({
      cursor: '{"last_event_id": 99, "offset": "2024-01-16T12:00:00"}',
      skipReason: null,
      error: null,
      dynamicPartitionsRequests: [],
      runRequests: [
        buildRunRequest({
          runKey: 'run-key-1',
          jobName: JOB_NAME,
          runConfigYaml: 'ops:\n  process_event:\n    config:\n      event_id: 99\n',
          tags: [
            buildPipelineTag({key: 'dagster/sensor_name', value: SENSOR_NAME}),
            buildPipelineTag({key: 'source', value: 'event_stream'}),
          ],
          assetSelection: [buildAssetKey({path: ['raw_events']})],
          assetChecks: [],
        }),
        buildRunRequest({
          runKey: 'run-key-2',
          jobName: 'my_organization__data_pipeline__extract_transform_load__weekly_aggregation_job',
          runConfigYaml: 'ops:\n  process_event:\n    config:\n      event_id: 100\n',
          tags: [buildPipelineTag({key: 'dagster/sensor_name', value: SENSOR_NAME})],
          assetSelection: [
            buildAssetKey({path: ['raw_events']}),
            buildAssetKey({path: ['processed_events']}),
          ],
          assetChecks: [],
        }),
        buildRunRequest({
          runKey: 'run-key-3',
          jobName:
            'really_long_prefix__customer_analytics__session_tracking__incremental_materialization_job_with_extra_suffix',
          runConfigYaml: 'ops:\n  process_event:\n    config:\n      event_id: 101\n',
          tags: [],
          assetSelection: null,
          assetChecks: [],
        }),
      ],
    }),
  }),
);

const skippedMock = buildSensorDryRunMock(
  buildDryRunInstigationTick({
    timestamp: Date.now() / 1000,
    evaluationResult: buildTickEvaluation({
      cursor: null,
      skipReason: 'No new events found since last poll',
      error: null,
      dynamicPartitionsRequests: [],
      runRequests: [],
    }),
  }),
);

const Wrapper = ({mocks, cursor = CURRENT_CURSOR}: {mocks: MockedResponse[]; cursor?: string}) => (
  <MemoryRouter>
    <MockedProvider mocks={mocks}>
      <WorkspaceProvider>
        <SensorDryRunDialog
          isOpen={true}
          onClose={() => {}}
          name={SENSOR_NAME}
          repoAddress={REPO_ADDRESS}
          currentCursor={cursor}
          jobName={JOB_NAME}
        />
      </WorkspaceProvider>
    </MockedProvider>
  </MemoryRouter>
);

export const InitialState = () => <Wrapper mocks={[withRunRequestsMock]} />;

export const WithRunRequests = () => <Wrapper mocks={[withRunRequestsMock]} />;

export const Skipped = () => <Wrapper mocks={[skippedMock]} />;

export const NoCursor = () => <Wrapper mocks={[withRunRequestsMock]} cursor="" />;
