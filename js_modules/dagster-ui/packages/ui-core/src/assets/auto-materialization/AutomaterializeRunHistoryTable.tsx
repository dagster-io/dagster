import {Box, ButtonGroup, CursorHistoryControls} from '@dagster-io/ui-components';
import styled from 'styled-components';

import {useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {RunTable} from '../../runs/RunTable';
import {RUNS_ROOT_QUERY} from '../../runs/RunsRoot';
import {RunsRootQuery, RunsRootQueryVariables} from '../../runs/types/RunsRoot.types';
import {useCursorPaginatedQuery} from '../../runs/useCursorPaginatedQuery';

const PAGE_SIZE = 15;

export const AutomaterializeRunHistoryTable = ({
  filterTags,
  setTableView,
}: {
  filterTags?: {key: string; value: string}[];
  setTableView: (view: 'evaluations' | 'runs') => void;
}) => {
  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    RunsRootQuery,
    RunsRootQueryVariables
  >({
    nextCursorForResult: (runs) => {
      if (runs.pipelineRunsOrError.__typename !== 'Runs') {
        return undefined;
      }
      return runs.pipelineRunsOrError.results[PAGE_SIZE - 1]?.id;
    },
    getResultArray: (data) => {
      if (!data || data.pipelineRunsOrError.__typename !== 'Runs') {
        return [];
      }
      return data.pipelineRunsOrError.results;
    },
    variables: {
      filter: {
        tags: [...(filterTags || []), {key: 'dagster/auto_materialize', value: 'true'}],
      },
    },
    query: RUNS_ROOT_QUERY,
    pageSize: PAGE_SIZE,
  });

  useQueryRefreshAtInterval(queryResult, 15 * 1000);

  const runData = (queryResult.data || queryResult.previousData)?.pipelineRunsOrError;

  return (
    <Box>
      <Wrapper>
        <Box padding={{vertical: 12, horizontal: 24}} margin={{top: 32}} border="top">
          <ButtonGroup
            activeItems={new Set(['runs'])}
            buttons={[
              {id: 'evaluations', label: 'Evaluations'},
              {id: 'runs', label: 'Runs'},
            ]}
            onClick={(id: 'evaluations' | 'runs') => {
              setTableView(id);
            }}
          />
        </Box>
        <RunTable runs={runData?.__typename === 'Runs' ? runData.results : []} />
      </Wrapper>
      <div style={{paddingBottom: '16px'}}>
        <CursorHistoryControls {...paginationProps} />
      </div>
    </Box>
  );
};

// Super hacky but easiest solution to position the action button
const Wrapper = styled.div`
  position: relative;
  > *:nth-child(2) {
    position: absolute;
    right: 0;
    top: 0;
  }
`;
