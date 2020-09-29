import {NonIdealState} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import gql from 'graphql-tag';
import * as React from 'react';
import {RouteComponentProps} from 'react-router';
import styled from 'styled-components/macro';

import {CursorPaginationControls} from 'src/CursorPaginationControls';
import {ScrollContainer} from 'src/ListComponents';
import {Loading} from 'src/Loading';
import {RunTable} from 'src/runs/RunTable';
import {RunsQueryRefetchContext} from 'src/runs/RunUtils';
import {
  RunFilterTokenType,
  RunsFilter,
  runsFilterForSearchTokens,
  useRunFiltering,
} from 'src/runs/RunsFilter';
import {useCursorPaginatedQuery} from 'src/runs/useCursorPaginatedQuery';
import {
  PipelineRunsRootQuery,
  PipelineRunsRootQueryVariables,
} from 'src/types/PipelineRunsRootQuery';

const PAGE_SIZE = 25;
const ENABLED_FILTERS: RunFilterTokenType[] = ['id', 'status', 'tag'];

export const PipelineRunsRoot: React.FunctionComponent<RouteComponentProps<{
  pipelinePath: string;
}>> = ({match}) => {
  const pipelineName = match.params.pipelinePath.split(':')[0];
  const [filterTokens, setFilterTokens] = useRunFiltering(ENABLED_FILTERS);

  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    PipelineRunsRootQuery,
    PipelineRunsRootQueryVariables
  >({
    query: PIPELINE_RUNS_ROOT_QUERY,
    pageSize: PAGE_SIZE,
    variables: {
      filter: {...runsFilterForSearchTokens(filterTokens), pipelineName},
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
      <ScrollContainer>
        <div style={{padding: '16px'}}>
          <div
            style={{
              display: 'flex',
              alignItems: 'baseline',
              justifyContent: 'space-between',
            }}
          >
            <Filters>
              <RunsFilter
                enabledFilters={ENABLED_FILTERS}
                tokens={[{token: 'pipeline', value: pipelineName}, ...filterTokens]}
                onChange={setFilterTokens}
                loading={queryResult.loading}
              />
            </Filters>
          </div>

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
              return (
                <>
                  <RunTable runs={displayed} onSetFilter={setFilterTokens} />
                  <CursorPaginationControls {...paginationProps} />
                </>
              );
            }}
          </Loading>
        </div>
      </ScrollContainer>
    </RunsQueryRefetchContext.Provider>
  );
};

const Filters = styled.div`
  float: right;
  display: flex;
  align-items: center;
  margin-bottom: 14px;
`;

export const PIPELINE_RUNS_ROOT_QUERY = gql`
  query PipelineRunsRootQuery($limit: Int, $cursor: String, $filter: PipelineRunsFilter!) {
    pipelineRunsOrError(limit: $limit, cursor: $cursor, filter: $filter) {
      ... on PipelineRuns {
        results {
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
