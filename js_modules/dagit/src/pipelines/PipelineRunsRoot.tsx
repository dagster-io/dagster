import {gql} from '@apollo/client';
import {NonIdealState, Tag} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';

import {QueryCountdown} from 'src/app/QueryCountdown';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {explorerPathFromString} from 'src/pipelines/PipelinePathUtils';
import {
  PipelineRunsRootQuery,
  PipelineRunsRootQueryVariables,
} from 'src/pipelines/types/PipelineRunsRootQuery';
import {RunTable, RUN_TABLE_RUN_FRAGMENT} from 'src/runs/RunTable';
import {RunsQueryRefetchContext} from 'src/runs/RunUtils';
import {
  RunFilterTokenType,
  RunsFilter,
  runsFilterForSearchTokens,
  useQueryPersistedRunFilters,
} from 'src/runs/RunsFilter';
import {POLL_INTERVAL, useCursorPaginatedQuery} from 'src/runs/useCursorPaginatedQuery';
import {Box} from 'src/ui/Box';
import {CursorPaginationControls} from 'src/ui/CursorControls';
import {Group} from 'src/ui/Group';
import {Loading} from 'src/ui/Loading';
import {Page} from 'src/ui/Page';
import {TokenizingFieldValue} from 'src/ui/TokenizingField';

const PAGE_SIZE = 25;
const ENABLED_FILTERS: RunFilterTokenType[] = ['status', 'tag'];

interface Props {
  pipelinePath: string;
}

export const PipelineRunsRoot: React.FC<Props> = (props) => {
  const {pipelinePath} = props;
  const {pipelineName, snapshotId} = explorerPathFromString(pipelinePath);

  useDocumentTitle(`Pipeline: ${pipelineName}`);

  const [filterTokens, setFilterTokens] = useQueryPersistedRunFilters(ENABLED_FILTERS);
  const permanentTokens = React.useMemo(() => {
    return [
      {token: 'pipeline', value: pipelineName},
      snapshotId ? {token: 'snapshotId', value: snapshotId} : null,
    ].filter(Boolean) as TokenizingFieldValue[];
  }, [pipelineName, snapshotId]);

  const allTokens = [...filterTokens, ...permanentTokens];

  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    PipelineRunsRootQuery,
    PipelineRunsRootQueryVariables
  >({
    query: PIPELINE_RUNS_ROOT_QUERY,
    pageSize: PAGE_SIZE,
    variables: {
      filter: {...runsFilterForSearchTokens(allTokens), pipelineName, snapshotId},
    },
    nextCursorForResult: (runs) => {
      if (runs.pipelineRunsOrError.__typename !== 'PipelineRuns') {
        return undefined;
      }
      return runs.pipelineRunsOrError.results[PAGE_SIZE]?.runId;
    },
    getResultArray: (data) => {
      if (!data || data.pipelineRunsOrError.__typename !== 'PipelineRuns') {
        return [];
      }
      return data.pipelineRunsOrError.results;
    },
  });

  return (
    <RunsQueryRefetchContext.Provider value={{refetch: queryResult.refetch}}>
      <Page>
        <Box
          flex={{alignItems: 'flex-start', justifyContent: 'space-between'}}
          margin={{bottom: 8}}
        >
          <Group direction="column" spacing={8}>
            <Group direction="row" spacing={8}>
              {permanentTokens.map(({token, value}) => (
                <Tag minimal key={token}>{`${token}:${value}`}</Tag>
              ))}
            </Group>
            <RunsFilter
              enabledFilters={ENABLED_FILTERS}
              tokens={filterTokens}
              onChange={setFilterTokens}
              loading={queryResult.loading}
            />
          </Group>
          <QueryCountdown pollInterval={POLL_INTERVAL} queryResult={queryResult} />
        </Box>

        <Loading queryResult={queryResult} allowStaleData={true}>
          {({pipelineRunsOrError}) => {
            if (pipelineRunsOrError.__typename !== 'PipelineRuns') {
              return (
                <NonIdealState
                  icon={IconNames.ERROR}
                  title="Query Error"
                  description={pipelineRunsOrError.message}
                />
              );
            }
            const runs = pipelineRunsOrError.results;
            const displayed = runs.slice(0, PAGE_SIZE);
            const {hasNextCursor, hasPrevCursor} = paginationProps;
            return (
              <>
                <RunTable runs={displayed} onSetFilter={setFilterTokens} />
                {hasNextCursor || hasPrevCursor ? (
                  <div style={{marginTop: '20px'}}>
                    <CursorPaginationControls {...paginationProps} />
                  </div>
                ) : null}
              </>
            );
          }}
        </Loading>
      </Page>
    </RunsQueryRefetchContext.Provider>
  );
};

const PIPELINE_RUNS_ROOT_QUERY = gql`
  query PipelineRunsRootQuery($limit: Int, $cursor: String, $filter: PipelineRunsFilter!) {
    pipelineRunsOrError(limit: $limit, cursor: $cursor, filter: $filter) {
      ... on PipelineRuns {
        results {
          id
          ...RunTableRunFragment
        }
      }
      ... on InvalidPipelineRunsFilterError {
        message
      }
      ... on PythonError {
        message
      }
    }
  }

  ${RUN_TABLE_RUN_FRAGMENT}
`;
