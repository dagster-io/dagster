import {gql} from '@apollo/client';

import {EXECUTION_PLAN_TO_GRAPH_FRAGMENT} from '../gantt/toGraphQueryItems';

import {LOGS_SCROLLING_TABLE_MESSAGE_FRAGMENT} from './LogsScrollingTable';
import {RUN_DETAILS_FRAGMENT} from './RunDetails';
import {RUN_METADATA_PROVIDER_MESSAGE_FRAGMENT} from './RunMetadataProvider';

export const RUN_FRAGMENT_FOR_REPOSITORY_MATCH = gql`
  fragment RunFragmentForRepositoryMatch on Run {
    id
    pipelineName
    pipelineSnapshotId
    parentPipelineSnapshotId
    repositoryOrigin {
      id
      repositoryName
      repositoryLocationName
    }
  }
`;

export const RUN_FRAGMENT = gql`
  fragment RunFragment on Run {
    id
    runConfigYaml
    runId
    canTerminate
    hasReExecutePermission
    hasTerminatePermission
    hasDeletePermission
    status
    mode
    tags {
      key
      value
    }
    assets {
      id
      key {
        path
      }
    }
    rootRunId
    parentRunId
    pipelineName
    solidSelection
    assetSelection {
      ... on AssetKey {
        path
      }
    }
    pipelineSnapshotId
    executionPlan {
      artifactsPersisted
      ...ExecutionPlanToGraphFragment
    }
    stepKeysToExecute
    updateTime
    stepStats {
      stepKey
      status
      startTime
      endTime
      attempts {
        startTime
        endTime
      }
      markers {
        startTime
        endTime
      }
    }
    ...RunFragmentForRepositoryMatch
    ...RunDetailsFragment
  }

  ${EXECUTION_PLAN_TO_GRAPH_FRAGMENT}
  ${RUN_FRAGMENT_FOR_REPOSITORY_MATCH}
  ${RUN_DETAILS_FRAGMENT}
`;

export const RUN_DAGSTER_RUN_EVENT_FRAGMENT = gql`
  fragment RunDagsterRunEventFragment on DagsterRunEvent {
    ... on MessageEvent {
      message
      timestamp
      level
      stepKey
    }

    ...LogsScrollingTableMessageFragment
    ...RunMetadataProviderMessageFragment
  }

  ${LOGS_SCROLLING_TABLE_MESSAGE_FRAGMENT}
  ${RUN_METADATA_PROVIDER_MESSAGE_FRAGMENT}
`;
