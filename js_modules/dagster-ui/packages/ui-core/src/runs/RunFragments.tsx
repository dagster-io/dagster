import {LOGS_SCROLLING_TABLE_MESSAGE_FRAGMENT} from './LogsScrollingTableMessageFragment';
import {RUN_METADATA_PROVIDER_MESSAGE_FRAGMENT} from './RunMetadataProvider';
import {RUN_TIMING_FRAGMENT} from './RunTimingDetails';
import {gql} from '../apollo-client';
import {EXECUTION_PLAN_TO_GRAPH_FRAGMENT} from '../gantt/toGraphQueryItems';

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
    hasRunMetricsEnabled
    status
    mode
    tags {
      key
      value
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
    assetCheckSelection {
      name
      assetKey {
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
    ...RunTimingFragment
  }

  ${EXECUTION_PLAN_TO_GRAPH_FRAGMENT}
  ${RUN_TIMING_FRAGMENT}
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
