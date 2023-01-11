import {useQuery} from '@apollo/client';
import {NonIdealState, Spinner} from '@dagster-io/ui';
import React from 'react';

import {graphql} from '../graphql';
import {RunTable} from '../runs/RunTable';
import {DagsterTag} from '../runs/RunTag';

interface PartitionRunListProps {
  pipelineName: string;
  partitionName: string;
}

export const PartitionRunList: React.FC<PartitionRunListProps> = (props) => {
  const {data, loading} = useQuery(PARTITION_RUN_LIST_QUERY, {
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
      <RunTable runs={data.pipelineRunsOrError.results} />
    </div>
  );
};

const PARTITION_RUN_LIST_QUERY = graphql(`
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
`);
