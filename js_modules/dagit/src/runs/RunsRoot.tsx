import {NonIdealState} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import gql from 'graphql-tag';
import * as React from 'react';
import {RouteComponentProps} from 'react-router';
import styled from 'styled-components/macro';

import {CursorPaginationControls} from 'src/CursorPaginationControls';
import {Header, ScrollContainer} from 'src/ListComponents';
import {Loading} from 'src/Loading';
import {RunTable} from 'src/runs/RunTable';
import {RunsQueryRefetchContext} from 'src/runs/RunUtils';
import {RunsFilter, runsFilterForSearchTokens, useRunFiltering} from 'src/runs/RunsFilter';
import {RunsRootQuery, RunsRootQueryVariables} from 'src/runs/types/RunsRootQuery';
import {useCursorPaginatedQuery} from 'src/runs/useCursorPaginatedQuery';

const PAGE_SIZE = 25;

export const RunsRoot: React.FunctionComponent<RouteComponentProps> = () => {
  const [filterTokens, setFilterTokens] = useRunFiltering();
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
    <RunsQueryRefetchContext.Provider value={{refetch: queryResult.refetch}}>
      <ScrollContainer>
        <div
          style={{
            display: 'flex',
            alignItems: 'baseline',
            justifyContent: 'space-between',
          }}
        >
          <Header>All Runs</Header>
          <Filters>
            <RunsFilter
              tokens={filterTokens}
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
            return (
              <>
                <RunTable
                  runs={pipelineRunsOrError.results.slice(0, PAGE_SIZE)}
                  onSetFilter={setFilterTokens}
                />
                <CursorPaginationControls {...paginationProps} />
              </>
            );
          }}
        </Loading>
      </ScrollContainer>
    </RunsQueryRefetchContext.Provider>
  );
};

export const RUNS_ROOT_QUERY = gql`
  query RunsRootQuery($limit: Int, $cursor: String, $filter: PipelineRunsFilter!) {
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

const Filters = styled.div`
  float: right;
  display: flex;
  align-items: center;
  margin-bottom: 14px;
`;
