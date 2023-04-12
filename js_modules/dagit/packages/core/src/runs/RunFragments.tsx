import {gql} from '@apollo/client';

import {EXECUTION_PLAN_TO_GRAPH_FRAGMENT} from '../gantt/toGraphQueryItems';

import {LOGS_SCROLLING_TABLE_MESSAGE_FRAGMENT} from './LogsScrollingTable';
import {RUN_DETAILS_FRAGMENT} from './RunDetails';
import {RUN_METADATA_PROVIDER_MESSAGE_FRAGMENT} from './RunMetadataProvider';

export const RUN_FRAGMENT = gql`
  fragment RunFragment on Run {
    id
    runConfigYaml
    canTerminate
    repositoryOrigin {
      id
      repositoryName
      repositoryLocationName
    }
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
    ...RunDetailsFragment
  }

  ${EXECUTION_PLAN_TO_GRAPH_FRAGMENT}
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

export const RUN_PAGE_FRAGMENT = gql`
  fragment RunPageFragment on Run {
    id
    parentPipelineSnapshotId
    ...RunFragment
  }

  ${RUN_FRAGMENT}
`;
