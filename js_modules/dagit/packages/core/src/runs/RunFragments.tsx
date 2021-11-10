import {gql} from '@apollo/client';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {EXECUTION_PLAN_TO_GRAPH_FRAGMENT} from '../gantt/toGraphQueryItems';

import {LOGS_SCROLLING_TABLE_MESSAGE_FRAGMENT} from './LogsScrollingTable';
import {RUN_DETAILS_FRAGMENT} from './RunDetails';
import {RUN_METADATA_PROVIDER_MESSAGE_FRAGMENT} from './RunMetadataProvider';

export const RUN_FRAGMENT_FOR_REPOSITORY_MATCH = gql`
  fragment RunFragmentForRepositoryMatch on Run {
    id
    pipeline {
      name
    }
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
      runConfig
      runId
      canTerminate
      status
      mode
      tags {
        key
        value
      }
      rootRunId
      parentRunId
      pipeline {
        __typename
        ... on PipelineReference {
          name
          solidSelection
        }
      }
      pipelineSnapshotId
      executionPlan {
        steps {
          key
          inputs {
            dependsOn {
              key
              outputs {
                name
                type {
                  name
                }
              }
            }
          }
        }
        artifactsPersisted
        ...ExecutionPlanToGraphFragment
      }
      stepKeysToExecute
      ...RunFragmentForRepositoryMatch
      ...RunDetailsFragment
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
