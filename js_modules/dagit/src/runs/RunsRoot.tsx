import {NonIdealState} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import gql from 'graphql-tag';
import * as React from 'react';
import {RouteComponentProps} from 'react-router';
import styled from 'styled-components/macro';

import {CursorPaginationControls} from '../CursorPaginationControls';
import {Header, ScrollContainer} from '../ListComponents';
import Loading from '../Loading';

import {RunTable} from './RunTable';
import {RunsQueryRefetchContext} from './RunUtils';
import {RunsFilter, runsFilterForSearchTokens, useRunFiltering} from './RunsFilter';
import {RunsRootQuery, RunsRootQueryVariables} from './types/RunsRootQuery';
import {useCursorPaginatedQuery} from './useCursorPaginatedQuery';

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
