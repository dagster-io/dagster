import {gql} from '@apollo/client';
import {NonIdealState} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import {RouteComponentProps} from 'react-router';

import {CursorPaginationControls} from 'src/CursorControls';
import {Loading} from 'src/Loading';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {RunTable} from 'src/runs/RunTable';
import {RunsQueryRefetchContext} from 'src/runs/RunUtils';
import {
  RunsFilter,
  runsFilterForSearchTokens,
  useQueryPersistedRunFilters,
} from 'src/runs/RunsFilter';
import {RunsRootQuery, RunsRootQueryVariables} from 'src/runs/types/RunsRootQuery';
import {useCursorPaginatedQuery} from 'src/runs/useCursorPaginatedQuery';
import {Group} from 'src/ui/Group';
import {Page} from 'src/ui/Page';
import {PageHeader} from 'src/ui/PageHeader';

const PAGE_SIZE = 25;

export const RunsRoot: React.FunctionComponent<RouteComponentProps> = () => {
  useDocumentTitle('Runs');
  const [filterTokens, setFilterTokens] = useQueryPersistedRunFilters();
  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    RunsRootQuery,
    RunsRootQueryVariables
  >({
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
    variables: {filter: runsFilterForSearchTokens(filterTokens)},
    query: RUNS_ROOT_QUERY,
    pageSize: PAGE_SIZE,
  });

  return (
    <Page>
      <PageHeader text="Runs" />
      <Group direction="vertical" spacing={8}>
        <RunsFilter
          tokens={filterTokens}
          onChange={setFilterTokens}
          loading={queryResult.loading}
        />
        <RunsQueryRefetchContext.Provider value={{refetch: queryResult.refetch}}>
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
              return (
                <>
                  <RunTable
                    runs={pipelineRunsOrError.results.slice(0, PAGE_SIZE)}
                    onSetFilter={setFilterTokens}
                  />
                  {pipelineRunsOrError.results.length > 0 ? (
                    <div style={{marginTop: '16px'}}>
                      <CursorPaginationControls {...paginationProps} />
                    </div>
                  ) : null}
                </>
              );
            }}
          </Loading>
        </RunsQueryRefetchContext.Provider>
      </Group>
    </Page>
  );
};

export const RUNS_ROOT_QUERY = gql`
  query RunsRootQuery($limit: Int, $cursor: String, $filter: PipelineRunsFilter!) {
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

  ${RunTable.fragments.RunTableRunFragment}
`;
