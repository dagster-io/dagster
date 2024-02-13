import {MockedResponse} from '@apollo/client/testing';

import {
  RunStatus,
  buildPipeline,
  buildRepository,
  buildRepositoryLocation,
  buildRepositoryOrigin,
  buildRun,
  buildWorkspace,
  buildWorkspaceLocationEntry,
} from '../../graphql/types';
import {ROOT_WORKSPACE_QUERY} from '../../workspace/WorkspaceContext';
import {RootWorkspaceQuery} from '../../workspace/types/WorkspaceContext.types';
import {PIPELINE_ENVIRONMENT_QUERY} from '../RunActionsMenu';
import {
  PipelineEnvironmentQuery,
  PipelineEnvironmentQueryVariables,
} from '../types/RunActionsMenu.types';

const LOCATION_NAME = 'my-origin';
const REPO_NAME = 'my-repo';
const JOB_NAME = 'job-bar';
const RUN_ID = 'run-foo-bar';
const SNAPSHOT_ID = 'snapshotID';

type RunConfigInput = {
  hasReExecutePermission: boolean;
};

export const buildRunActionsMenuFragment = ({hasReExecutePermission}: RunConfigInput) => {
  return buildRun({
    id: RUN_ID,
    status: RunStatus.SUCCESS,
    stepKeysToExecute: null,
    canTerminate: true,
    hasDeletePermission: true,
    hasReExecutePermission,
    hasTerminatePermission: true,
    mode: 'default',
    rootRunId: 'abcdef12',
    parentRunId: null,
    pipelineSnapshotId: SNAPSHOT_ID,
    pipelineName: JOB_NAME,
    repositoryOrigin: buildRepositoryOrigin({
      id: 'repo',
      repositoryName: REPO_NAME,
      repositoryLocationName: LOCATION_NAME,
    }),
    solidSelection: null,
    assetSelection: null,
    assetCheckSelection: null,
    tags: [],
    startTime: 123,
    endTime: 456,
    updateTime: 789,
  });
};

export const buildMockRootWorkspaceQuery = (): MockedResponse<RootWorkspaceQuery> => {
  return {
    request: {
      query: ROOT_WORKSPACE_QUERY,
    },
    result: {
      data: {
        __typename: 'Query',
        workspaceOrError: buildWorkspace({
          id: 'workspace',
          locationEntries: [
            buildWorkspaceLocationEntry({
              id: LOCATION_NAME,
              locationOrLoadError: buildRepositoryLocation({
                id: LOCATION_NAME,
                repositories: [
                  buildRepository({
                    id: REPO_NAME,
                    name: REPO_NAME,
                    pipelines: [
                      buildPipeline({
                        id: JOB_NAME,
                        name: JOB_NAME,
                        pipelineSnapshotId: SNAPSHOT_ID,
                      }),
                    ],
                  }),
                ],
              }),
            }),
          ],
        }),
      },
    },
  };
};

export const buildPipelineEnvironmentQuery = (
  runConfig: RunConfigInput,
): MockedResponse<PipelineEnvironmentQuery, PipelineEnvironmentQueryVariables> => {
  return {
    request: {
      query: PIPELINE_ENVIRONMENT_QUERY,
      variables: {
        runId: RUN_ID,
      },
    },
    result: {
      data: {
        __typename: 'Query',
        pipelineRunOrError: buildRunActionsMenuFragment(runConfig),
      },
    },
  };
};
