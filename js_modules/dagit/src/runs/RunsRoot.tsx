import {gql, NetworkStatus} from '@apollo/client';
import {Colors, NonIdealState, Spinner, Tab, Tabs, Tag} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import {isEqual} from 'lodash';
import * as React from 'react';
import {RouteComponentProps} from 'react-router';
import styled from 'styled-components';

import {CursorPaginationControls} from 'src/CursorControls';
import {Loading} from 'src/Loading';
import {TokenizingFieldValue} from 'src/TokenizingField';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {RunTable} from 'src/runs/RunTable';
import {RunsQueryRefetchContext} from 'src/runs/RunUtils';
import {
  RunsFilter,
  runsFilterForSearchTokens,
  useQueryPersistedRunFilters,
} from 'src/runs/RunsFilter';
import {CountFragment} from 'src/runs/types/CountFragment';
import {RunsRootQuery, RunsRootQueryVariables} from 'src/runs/types/RunsRootQuery';
import {POLL_INTERVAL, useCursorPaginatedQuery} from 'src/runs/useCursorPaginatedQuery';
import {PipelineRunStatus} from 'src/types/globalTypes';
import {Box} from 'src/ui/Box';
import {ButtonLink} from 'src/ui/ButtonLink';
import {useCountdown} from 'src/ui/Countdown';
import {Group} from 'src/ui/Group';
import {Page} from 'src/ui/Page';
import {RefreshableCountdown} from 'src/ui/RefreshableCountdown';
import {Heading} from 'src/ui/Text';

const PAGE_SIZE = 25;

const queuedStatuses = new Set([PipelineRunStatus.QUEUED]);
const inProgressStatuses = new Set([PipelineRunStatus.STARTED, PipelineRunStatus.STARTING]);
const doneStatuses = new Set([PipelineRunStatus.FAILURE, PipelineRunStatus.SUCCESS]);

const selectedTabId = (filterTokens: TokenizingFieldValue[]) => {
  const statusTokens = new Set(
    filterTokens.filter((token) => token.token === 'status').map((token) => token.value),
  );
  if (isEqual(queuedStatuses, statusTokens)) {
    return 'queued';
  }
  if (isEqual(inProgressStatuses, statusTokens)) {
    return 'in-progress';
  }
  if (isEqual(doneStatuses, statusTokens)) {
    return 'done';
  }
  return 'all';
};

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
    variables: {
      filter: runsFilterForSearchTokens(filterTokens),
      queuedFilter: {statuses: Array.from(queuedStatuses)},
      inProgressFilter: {statuses: Array.from(inProgressStatuses)},
    },
    query: RUNS_ROOT_QUERY,
    pageSize: PAGE_SIZE,
  });

  const countdownStatus = queryResult.networkStatus === NetworkStatus.ready ? 'counting' : 'idle';
  const timeRemaining = useCountdown({
    duration: POLL_INTERVAL,
    status: countdownStatus,
  });

  const setStatusFilter = (statuses: PipelineRunStatus[]) => {
    const tokensMinusStatus = filterTokens.filter((token) => token.token !== 'status');
    const statusTokens = statuses.map((status) => ({token: 'status', value: status}));
    setFilterTokens([...statusTokens, ...tokensMinusStatus]);
  };

  const selectedTab = selectedTabId(filterTokens);
  const tabColor = (match: string) =>
    selectedTab === match ? Colors.BLUE1 : {link: Colors.GRAY2, hover: Colors.BLUE1};

  const countdownRefreshing = countdownStatus === 'idle' || timeRemaining === 0;

  return (
    <Page>
      <Group direction="vertical" spacing={8}>
        <Heading>Runs</Heading>
        <Box
          border={{side: 'bottom', width: 1, color: Colors.LIGHT_GRAY3}}
          flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'flex-end'}}
        >
          <Tabs selectedTabId={selectedTab} id="run-tabs">
            <Tab
              title={
                <TabButton
                  color={tabColor('all')}
                  underline="never"
                  onClick={() => setStatusFilter([])}
                >
                  All runs
                </TabButton>
              }
              id="all"
            />
            <Tab
              title={
                <TabButton
                  color={tabColor('queued')}
                  underline="never"
                  onClick={() => setStatusFilter(Array.from(queuedStatuses))}
                >
                  <Group direction="horizontal" spacing={4} alignItems="center">
                    <div>Queued</div>
                    <CountTag
                      loading={queryResult.loading}
                      fragment={
                        queryResult.data?.queuedCount?.__typename === 'PipelineRuns'
                          ? queryResult.data?.queuedCount
                          : undefined
                      }
                    />
                  </Group>
                </TabButton>
              }
              id="queued"
            />
            <Tab
              title={
                <TabButton
                  color={tabColor('in-progress')}
                  underline="never"
                  onClick={() => setStatusFilter(Array.from(inProgressStatuses))}
                >
                  <Group direction="horizontal" spacing={4} alignItems="center">
                    <div>In progress</div>
                    <CountTag
                      loading={queryResult.loading}
                      fragment={
                        queryResult.data?.inProgressCount?.__typename === 'PipelineRuns'
                          ? queryResult.data?.inProgressCount
                          : undefined
                      }
                    />
                  </Group>
                </TabButton>
              }
              id="in-progress"
            />
            <Tab
              title={
                <TabButton
                  color={tabColor('done')}
                  underline="never"
                  onClick={() => setStatusFilter(Array.from(doneStatuses))}
                >
                  Done
                </TabButton>
              }
              id="done"
            />
          </Tabs>
          <Box padding={{bottom: 8}}>
            <RefreshableCountdown
              refreshing={countdownRefreshing}
              seconds={Math.floor(timeRemaining / 1000)}
              onRefresh={() => queryResult.refetch()}
            />
          </Box>
        </Box>
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

const COUNT_FRAGMENT = gql`
  fragment CountFragment on PipelineRuns {
    count
  }
`;

const RUNS_ROOT_QUERY = gql`
  query RunsRootQuery(
    $limit: Int
    $cursor: String
    $filter: PipelineRunsFilter!
    $queuedFilter: PipelineRunsFilter!
    $inProgressFilter: PipelineRunsFilter!
  ) {
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
    queuedCount: pipelineRunsOrError(filter: $queuedFilter) {
      ...CountFragment
    }
    inProgressCount: pipelineRunsOrError(filter: $inProgressFilter) {
      ...CountFragment
    }
  }

  ${RunTable.fragments.RunTableRunFragment}
  ${COUNT_FRAGMENT}
`;

const TabButton = styled(ButtonLink)`
  line-height: 34px;
`;

interface CountTagProps {
  loading: boolean;
  fragment: CountFragment | undefined;
}

const CountTag = (props: CountTagProps) => {
  const {loading, fragment} = props;
  if (loading) {
    return (
      <CountTagStyled minimal intent="none">
        <Spinner size={10} />
      </CountTagStyled>
    );
  }
  if (typeof fragment?.count === 'number') {
    return (
      <CountTagStyled minimal intent="none">
        {fragment.count}
      </CountTagStyled>
    );
  }
  return null;
};

const CountTagStyled = styled(Tag)`
  min-width: 24px;
`;
