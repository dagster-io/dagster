import {gql} from '@apollo/client';

import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {RunMetadataProvider} from 'src/RunMetadataProvider';
import {GanttChart} from 'src/gantt/GanttChart';
import {LogsScrollingTable} from 'src/runs/LogsScrollingTable';
import {RUN_DETAILS_FRAGMENT} from 'src/runs/RunDetails';
import {RunStatusToPageAttributes} from 'src/runs/RunStatusToPageAttributes';

export const RUN_FRAGMENT_FOR_REPOSITORY_MATCH = gql`
  fragment RunFragmentForRepositoryMatch on PipelineRun {
    id
    pipeline {
      name
    }
    pipelineSnapshotId
    repositoryOrigin {
      repositoryName
      repositoryLocationName
    }
  }
`;

export const RunFragments = {
  RunFragment: gql`
    fragment RunFragment on PipelineRun {
      ...RunStatusPipelineRunFragment

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
        ...GanttChartExecutionPlanFragment
      }
      stepKeysToExecute
      ...RunFragmentForRepositoryMatch
      ...RunDetailsFragment
    }

    ${RunStatusToPageAttributes.fragments.RunStatusPipelineRunFragment}
    ${GanttChart.fragments.GanttChartExecutionPlanFragment}
    ${RUN_FRAGMENT_FOR_REPOSITORY_MATCH}
    ${RUN_DETAILS_FRAGMENT}
  `,
  RunPipelineRunEventFragment: gql`
    fragment RunPipelineRunEventFragment on PipelineRunEvent {
      ... on MessageEvent {
        message
        timestamp
        level
        stepKey
      }

      ...LogsScrollingTableMessageFragment
      ...RunMetadataProviderMessageFragment
    }

    ${RunMetadataProvider.fragments.RunMetadataProviderMessageFragment}
    ${LogsScrollingTable.fragments.LogsScrollingTableMessageFragment}
    ${PythonErrorInfo.fragments.PythonErrorFragment}
  `,
};
