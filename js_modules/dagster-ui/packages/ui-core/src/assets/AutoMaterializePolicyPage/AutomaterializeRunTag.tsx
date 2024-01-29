import {gql, useQuery} from '@apollo/client';
import {Tag} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import {RunStatusOnlyQuery, RunStatusOnlyQueryVariables} from './types/AutomaterializeRunTag.types';
import {RunStatusTagWithID} from '../../runs/RunStatusTag';

interface Props {
  runId: string;
}

export const AutomaterializeRunTag = ({runId}: Props) => {
  const {data, loading} = useQuery<RunStatusOnlyQuery, RunStatusOnlyQueryVariables>(
    RUN_STATUS_ONLY,
    {
      variables: {runId},
    },
  );

  if (loading && !data) {
    return <Tag icon="spinner">Loading</Tag>;
  }

  const run = data?.runOrError;
  if (run?.__typename !== 'Run') {
    return (
      <Tag icon="error" intent="danger">
        Run not found
      </Tag>
    );
  }

  return (
    <Link to={`/runs/${runId}`}>
      <RunStatusTagWithID runId={runId} status={run.status} />
    </Link>
  );
};

export const RUN_STATUS_ONLY = gql`
  query RunStatusOnlyQuery($runId: ID!) {
    runOrError(runId: $runId) {
      ... on Run {
        id
        status
      }
    }
  }
`;
