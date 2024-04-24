import {gql, useQuery} from '@apollo/client';
import {
  Body,
  Box,
  Colors,
  Group,
  Icon,
  NonIdealState,
  Spinner,
  Tooltip,
} from '@dagster-io/ui-components';

import {LaunchedRunListQuery, LaunchedRunListQueryVariables} from './types/InstigationTick.types';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {RUN_TABLE_RUN_FRAGMENT, RunTable} from '../runs/RunTable';

export const RunList = ({runIds}: {runIds: string[]}) => {
  const {data, loading} = useQuery<LaunchedRunListQuery, LaunchedRunListQueryVariables>(
    LAUNCHED_RUN_LIST_QUERY,
    {
      variables: {
        filter: {
          runIds,
        },
      },
    },
  );

  if (loading || !data) {
    return (
      <Box padding={32}>
        <Spinner purpose="section" />
      </Box>
    );
  }

  if (data.pipelineRunsOrError.__typename !== 'Runs') {
    return (
      <Box padding={32}>
        <NonIdealState
          icon="error"
          title="An error occurred"
          description={data.pipelineRunsOrError.message}
        />
      </Box>
    );
  }

  return (
    <Box padding={{bottom: 8}}>
      <RunTable runs={data.pipelineRunsOrError.results} />
    </Box>
  );
};

export const FailedRunList = ({originRunIds}: {originRunIds?: string[]}) => {
  if (!originRunIds || !originRunIds.length) {
    return null;
  }
  return (
    <Group direction="column" spacing={16}>
      <Box padding={12} border={{side: 'bottom', color: Colors.textLighter()}}>
        <Body>
          Failed Runs
          <Tooltip content="Failed runs this tick reacted on and reported back to.">
            <Icon name="info" color={Colors.textLight()} />
          </Tooltip>
        </Body>

        <RunList runIds={originRunIds} />
      </Box>
      <Box padding={12} margin={{bottom: 8}}>
        <Body>
          Requested Runs
          <Tooltip content="Runs launched by the run requests in this tick.">
            <Icon name="info" color={Colors.textLight()} />
          </Tooltip>
        </Body>
        <NonIdealState
          icon="sensors"
          title="No runs to display"
          description="This sensor does not target a pipeline or job."
        />
      </Box>
    </Group>
  );
};

export const TICK_TAG_FRAGMENT = gql`
  fragment TickTagFragment on InstigationTick {
    id
    status
    timestamp
    skipReason
    runIds
    runKeys
    error {
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

const LAUNCHED_RUN_LIST_QUERY = gql`
  query LaunchedRunListQuery($filter: RunsFilter!) {
    pipelineRunsOrError(filter: $filter, limit: 500) {
      ... on PipelineRuns {
        results {
          ...RunTableRunFragment
          id
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
