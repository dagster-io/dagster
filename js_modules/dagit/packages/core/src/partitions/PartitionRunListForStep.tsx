import {gql, useQuery} from '@apollo/client';
import {NonIdealState, Spinner} from '@dagster-io/ui';
import React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {RunTable, RUN_TABLE_RUN_FRAGMENT} from '../runs/RunTable';
import {DagsterTag} from '../runs/RunTag';
import {StepEventStatus} from '../types/globalTypes';

import {
  PartitionRunListForStepQuery,
  PartitionRunListForStepQueryVariables,
} from './types/PartitionRunListForStepQuery';

interface StepStats {
  startTime: number | null;
  endTime: number | null;
  status: StepEventStatus | null;
  materializations: Record<string, unknown>[];
  expectationResults: {success: boolean}[];
}

interface PartitionRunListForStepProps {
  pipelineName: string;
  partitionName: string;
  stepName: string;
  stepStatsByRunId: {
    [runId: string]: StepStats;
  };
}

export const PartitionRunListForStep: React.FC<PartitionRunListForStepProps> = (props) => {
  const {data, loading} = useQuery<
    PartitionRunListForStepQuery,
    PartitionRunListForStepQueryVariables
  >(PARTITION_RUN_LIST_FOR_STEP_QUERY, {
    variables: {
      filter: {
        pipelineName: props.pipelineName,
        tags: [{key: DagsterTag.Partition, value: props.partitionName}],
      },
    },
  });

  if (loading || !data) {
    return <Spinner purpose="section" />;
  }

  if (data.pipelineRunsOrError.__typename !== 'Runs') {
    return (
      <NonIdealState
        icon="error"
        title="Query Error"
        description={data.pipelineRunsOrError.message}
      />
    );
  }
  return (
    <div>
      <RunTable
        runs={data.pipelineRunsOrError.results}
        additionalColumnHeaders={[
          <th key="context" style={{maxWidth: 150}}>
            Step Info
          </th>,
        ]}
      />
    </div>
  );
};

const PARTITION_RUN_LIST_FOR_STEP_QUERY = gql`
  query PartitionRunListForStepQuery($filter: RunsFilter!) {
    pipelineRunsOrError(filter: $filter, limit: 500) {
      ... on PipelineRuns {
        results {
          ...RunTableRunFragment
          id
          runId
        }
      }
      ... on InvalidPipelineRunsFilterError {
        message
      }
      ...PythonErrorFragment
    }
  }
  ${RUN_TABLE_RUN_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
