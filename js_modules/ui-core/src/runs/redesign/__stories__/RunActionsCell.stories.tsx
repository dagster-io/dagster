import {MockedProvider} from '@apollo/client/testing';
import {showToast} from '@dagster-io/ui-components';

import {
  buildAssetKey,
  buildExecutionPlan,
  buildPipeline,
  buildRepository,
  buildRepositoryLocation,
  buildRun,
  buildWorkspaceLocationEntry,
} from '../../../graphql/builders';
import {RunStatus} from '../../../graphql/types';
import {buildQueryMock} from '../../../testing/mocking';
import {WorkspaceProvider} from '../../../workspace/WorkspaceContext/WorkspaceContext';
import {buildWorkspaceMocks} from '../../../workspace/WorkspaceContext/__fixtures__/Workspace.fixtures';
import {RunActionsCell} from '../RunActionsCell';
import {RUN_ACTIONS_MENU_QUERY} from '../RunActionsMenuQuery';
import {runEntry} from '../__fixtures__/RunsFeedEntries.fixtures';
import {
  RunActionsMenuQuery,
  RunActionsMenuQueryVariables,
} from '../types/RunActionsMenuQuery.types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Runs Redesign/RunActionsCell',
  component: RunActionsCell,
};

const RUN_ID = 'a1b2c3d4-1111-2222-3333-444455556666';
const JOB_NAME = 'daily_etl';
const SNAPSHOT_ID = 'snapshot-id';

const menuMock = buildQueryMock<RunActionsMenuQuery, RunActionsMenuQueryVariables>({
  query: RUN_ACTIONS_MENU_QUERY,
  variables: {runId: RUN_ID},
  data: {
    runOrError: buildRun({
      id: RUN_ID,
      parentPipelineSnapshotId: null,
      runConfigYaml: 'ops:\n  load_sales:\n    config:\n      limit: 10\n',
      assetSelection: null,
      assetCheckSelection: null,
      executionPlan: buildExecutionPlan({assetKeys: [buildAssetKey({path: ['sales', 'daily']})]}),
    }),
  },
  maxUsageCount: Number.POSITIVE_INFINITY,
});

const workspaceMocks = buildWorkspaceMocks(
  [
    buildWorkspaceLocationEntry({
      id: 'my_location',
      name: 'my_location',
      locationOrLoadError: buildRepositoryLocation({
        id: 'my_location',
        name: 'my_location',
        repositories: [
          buildRepository({
            id: 'my_repo',
            name: 'my_repo',
            pipelines: [
              buildPipeline({
                id: JOB_NAME,
                name: JOB_NAME,
                isJob: true,
                pipelineSnapshotId: SNAPSHOT_ID,
              }),
            ],
          }),
        ],
      }),
    }),
  ],
  {maxUsageCount: Number.POSITIVE_INFINITY},
);

export const QueuedRun = () => (
  <MockedProvider mocks={[menuMock, ...workspaceMocks]}>
    <WorkspaceProvider>
      <div style={{display: 'flex', justifyContent: 'flex-end', width: 420, padding: 16}}>
        <RunActionsCell
          run={runEntry({
            id: RUN_ID,
            runStatus: RunStatus.QUEUED,
            startTime: null,
            endTime: null,
            jobName: JOB_NAME,
            pipelineSnapshotId: SNAPSHOT_ID,
            hasReExecutePermission: true,
            hasTerminatePermission: true,
            hasDeletePermission: true,
          })}
          onOpenRunDialog={() => {
            showToast({message: 'The run dialog opens here.', intent: 'none'});
          }}
        />
      </div>
    </WorkspaceProvider>
  </MockedProvider>
);
