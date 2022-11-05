import {gql, useQuery} from '@apollo/client';
import {NonIdealState, Spinner} from '@dagster-io/ui';
import React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {RunTable, RUN_TABLE_RUN_FRAGMENT} from '../runs/RunTable';
import {DagsterTag} from '../runs/RunTag';

import {PartitionRunListQuery, PartitionRunListQueryVariables} from './types/PartitionRunListQuery';

interface PartitionRunListProps {
  pipelineName: string;
  partitionName: string;
}

export const PartitionRunList: React.FC<PartitionRunListProps> = (props) => {
  const {data, loading} = useQuery<PartitionRunListQuery, PartitionRunListQueryVariables>(
    PARTITION_RUN_LIST_QUERY,
    {
      variables: {
        filter: {
          pipelineName: props.pipelineName,
          tags: [{key: DagsterTag.Partition, value: props.partitionName}],
        },
      },
    },
  );

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
      <RunTable runs={data.pipelineRunsOrError.results} />
    </div>
  );
};

const PARTITION_RUN_LIST_QUERY = gql`
  query PartitionRunListQuery($filter: RunsFilter!) {
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
