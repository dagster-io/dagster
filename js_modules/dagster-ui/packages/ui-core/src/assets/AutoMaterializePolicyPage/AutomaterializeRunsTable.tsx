import {gql, useQuery} from '@apollo/client';
import {Body2, Box, Colors, Mono, Table} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import {
  AutomaterializeRunsQuery,
  AutomaterializeRunsQueryVariables,
} from './types/AutomaterializeRunsTable.types';
import {PYTHON_ERROR_FRAGMENT} from '../../app/PythonErrorFragment';
import {PythonErrorInfo} from '../../app/PythonErrorInfo';
import {RunStatusTagWithStats} from '../../runs/RunStatusTag';
import {RUN_TIME_FRAGMENT, RunStateSummary, RunTime, titleForRun} from '../../runs/RunUtils';

export const AutomaterializeRunsTable = ({runIds}: {runIds: string[]}) => {
  const {data, loading, error} = useQuery<
    AutomaterializeRunsQuery,
    AutomaterializeRunsQueryVariables
  >(AUTOMATERIALIZE_RUNS_QUERY, {
    variables: {
      filter: {
        runIds,
      },
    },
    skip: !runIds.length,
  });

  if (!runIds.length) {
    return (
      <Body2 color={Colors.textLighter()} style={{paddingBottom: 32}}>
        None
      </Body2>
    );
  }

  if (error) {
    return <Body2>An error occurred fetching runs. Check your network status</Body2>;
  }

  if (loading || !data) {
    return null;
  }

  if (data.runsOrError.__typename === 'PythonError') {
    return <PythonErrorInfo error={data?.runsOrError} />;
  }

  if (data.runsOrError.__typename === 'InvalidPipelineRunsFilterError') {
    return <Body2>{data.runsOrError.message}</Body2>;
  }

  return (
    <Box>
      <Table>
        <thead>
          <tr>
            <th style={{minWidth: 150}}>Run ID</th>
            <th style={{minWidth: 150}}>Created date</th>
            <th style={{minWidth: 100}}>Status</th>
            <th style={{minWidth: 150}}>Duration</th>
          </tr>
        </thead>
        <tbody>
          {data.runsOrError.results.map((run) => (
            <tr key={run.id}>
              <td>
                <Link to={`/runs/${run.id}`}>
                  <Mono>{titleForRun(run)}</Mono>
                </Link>
              </td>
              <td>
                <RunTime run={run} />
              </td>
              <td>
                <RunStatusTagWithStats runId={run.runId} status={run.status} />
              </td>
              <td>
                <RunStateSummary run={run} />
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Box>
  );
};

const AUTOMATERIALIZE_RUNS_QUERY = gql`
  query AutomaterializeRunsQuery($filter: RunsFilter) {
    runsOrError(filter: $filter) {
      ... on Runs {
        results {
          id
          ...AutomaterializeRunFragment
        }
      }
      ... on InvalidPipelineRunsFilterError {
        message
      }
      ...PythonErrorFragment
    }
  }

  fragment AutomaterializeRunFragment on Run {
    id
    runId
    ...RunTimeFragment
  }

  ${PYTHON_ERROR_FRAGMENT}
  ${RUN_TIME_FRAGMENT}
`;
