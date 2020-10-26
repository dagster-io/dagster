import {gql} from '@apollo/client';

import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {RunMetadataProvider} from 'src/RunMetadataProvider';
import {GaantChart} from 'src/gaant/GaantChart';
import {LogsScrollingTable} from 'src/runs/LogsScrollingTable';
import {RunStatusToPageAttributes} from 'src/runs/RunStatusToPageAttributes';

export const RunFragments = {
  RunFragment: gql`
    fragment RunFragment on PipelineRun {
      ...RunStatusPipelineRunFragment

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
        ...GaantChartExecutionPlanFragment
      }
      stepKeysToExecute
    }

    ${RunStatusToPageAttributes.fragments.RunStatusPipelineRunFragment}
    ${GaantChart.fragments.GaantChartExecutionPlanFragment}
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
