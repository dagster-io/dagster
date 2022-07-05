import {gql} from '@apollo/client';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {EXECUTION_PLAN_TO_GRAPH_FRAGMENT} from '../gantt/toGraphQueryItems';

import {LOGS_SCROLLING_TABLE_MESSAGE_FRAGMENT} from './LogsScrollingTable';
import {RUN_DETAILS_FRAGMENT} from './RunDetails';
import {RUN_METADATA_PROVIDER_MESSAGE_FRAGMENT} from './RunMetadataProvider';

export const RUN_FRAGMENT_FOR_REPOSITORY_MATCH = gql`
  fragment RunFragmentForRepositoryMatch on Run {
    id
    pipelineName
    pipelineSnapshotId
    repositoryOrigin {
      id
      repositoryName
      repositoryLocationName
    }
  }
`;

export const RunFragments = {
  RunFragment: gql`
    fragment RunFragment on Run {
      id
      runConfigYaml
      runId
      canTerminate
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
      ...RunFragmentForRepositoryMatch
      ...RunDetailsFragment
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
    }

    ${EXECUTION_PLAN_TO_GRAPH_FRAGMENT}
    ${RUN_FRAGMENT_FOR_REPOSITORY_MATCH}
    ${RUN_DETAILS_FRAGMENT}
  `,
  RunDagsterRunEventFragment: gql`
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

    ${RUN_METADATA_PROVIDER_MESSAGE_FRAGMENT}
    ${LOGS_SCROLLING_TABLE_MESSAGE_FRAGMENT}
    ${PYTHON_ERROR_FRAGMENT}
  `,
};
