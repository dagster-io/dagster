import * as React from 'react';

import Loading from './Loading';
import {RouteComponentProps} from 'react-router';
import {RunTable} from './runs/RunTable';
import {PipelineRunsRootQuery, PipelineRunsRootQueryVariables} from './types/PipelineRunsRootQuery';
import {
  RunsFilter,
  RunFilterTokenType,
  useRunFiltering,
  runsFilterForSearchTokens,
} from './runs/RunsFilter';

import gql from 'graphql-tag';
import styled from 'styled-components/macro';
import {IconNames} from '@blueprintjs/icons';
import {NonIdealState} from '@blueprintjs/core';
import {ScrollContainer, Header} from './ListComponents';
import {RunsQueryRefetchContext} from './runs/RunUtils';
import {useCursorPaginatedQuery} from './runs/useCursorPaginatedQuery';
import {CursorPaginationControls} from './CursorPaginationControls';

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
      if (runs.pipelineRunsOrError.__typename !== 'PipelineRuns') return undefined;
      return runs.pipelineRunsOrError.results[PAGE_SIZE]?.runId;
    },
    getResultArray: (data) => {
      if (!data || data.pipelineRunsOrError.__typename !== 'PipelineRuns') return [];
      return data.pipelineRunsOrError.results;
    },
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
          <Header>{`Runs`}</Header>
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
