import {gql, useQuery} from '@apollo/client';
import isEqual from 'lodash/isEqual';
import * as React from 'react';
import {Link, RouteComponentProps} from 'react-router-dom';

import {QueryCountdown} from '../app/QueryCountdown';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {PipelineRunStatus} from '../types/globalTypes';
import {Alert} from '../ui/Alert';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {CursorPaginationControls} from '../ui/CursorControls';
import {Group} from '../ui/Group';
import {Loading} from '../ui/Loading';
import {NonIdealState} from '../ui/NonIdealState';
import {Page} from '../ui/Page';
import {PageHeader} from '../ui/PageHeader';
import {Tab, Tabs} from '../ui/Tabs';
import {Heading} from '../ui/Text';
import {TokenizingFieldValue} from '../ui/TokenizingField';

import {AllScheduledTicks} from './AllScheduledTicks';
import {doneStatuses, inProgressStatuses, queuedStatuses} from './RunStatuses';
import {RunTable, RUN_TABLE_RUN_FRAGMENT} from './RunTable';
import {RunsQueryRefetchContext} from './RunUtils';
import {
  RunFilterTokenType,
  RunsFilter,
  runsFilterForSearchTokens,
  useQueryPersistedRunFilters,
} from './RunsFilter';
import {QueueDaemonStatusQuery} from './types/QueueDaemonStatusQuery';
import {RunsRootQuery, RunsRootQueryVariables} from './types/RunsRootQuery';
import {POLL_INTERVAL, useCursorPaginatedQuery} from './useCursorPaginatedQuery';

const PAGE_SIZE = 25;

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

export const RunsRoot: React.FC<RouteComponentProps> = () => {
  useDocumentTitle('Runs');
  const [filterTokens, setFilterTokens] = useQueryPersistedRunFilters();
  const filter = runsFilterForSearchTokens(filterTokens);
  const [showScheduled, setShowScheduled] = React.useState(false);

  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    RunsRootQuery,
    RunsRootQueryVariables
  >({
    nextCursorForResult: (runs) => {
      if (runs.pipelineRunsOrError.__typename !== 'PipelineRuns') {
        return undefined;
      }
      return runs.pipelineRunsOrError.results[PAGE_SIZE - 1]?.runId;
    },
    getResultArray: (data) => {
      if (!data || data.pipelineRunsOrError.__typename !== 'PipelineRuns') {
        return [];
      }
      return data.pipelineRunsOrError.results;
    },
    variables: {
      filter,
      queuedFilter: {...filter, statuses: Array.from(queuedStatuses)},
      inProgressFilter: {...filter, statuses: Array.from(inProgressStatuses)},
    },
    query: RUNS_ROOT_QUERY,
    pageSize: PAGE_SIZE,
  });

  const setStatusFilter = (statuses: PipelineRunStatus[]) => {
    const tokensMinusStatus = filterTokens.filter((token) => token.token !== 'status');
    const statusTokens = statuses.map((status) => ({token: 'status', value: status}));
    setFilterTokens([...statusTokens, ...tokensMinusStatus]);
    setShowScheduled(false);
  };

  const selectedTab = showScheduled ? 'scheduled' : selectedTabId(filterTokens);
  const enabledFilters: RunFilterTokenType[] = [
    'status',
    'tag',
    'snapshotId',
    'id',
    'job',
    'pipeline',
  ];

  return (
    <Page>
      <PageHeader
        title={<Heading>Runs</Heading>}
        tabs={
          <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'flex-end'}}>
            <Tabs selectedTabId={selectedTab} id="run-tabs">
              <Tab title="All runs" onClick={() => setStatusFilter([])} id="all" />
              <Tab
                title="Queued"
                count={
                  queryResult.data?.queuedCount?.__typename === 'PipelineRuns'
                    ? queryResult.data?.queuedCount.count
                    : 'indeterminate'
                }
                onClick={() => setStatusFilter(Array.from(queuedStatuses))}
                id="queued"
              />
              <Tab
                title="In progress"
                count={
                  queryResult.data?.inProgressCount?.__typename === 'PipelineRuns'
                    ? queryResult.data?.inProgressCount.count
                    : 'indeterminate'
                }
                onClick={() => setStatusFilter(Array.from(inProgressStatuses))}
                id="in-progress"
              />
              <Tab
                title="Done"
                onClick={() => setStatusFilter(Array.from(doneStatuses))}
                id="done"
              />
              <Tab title="Scheduled" onClick={() => setShowScheduled(true)} id="scheduled" />
            </Tabs>
            <Box padding={{bottom: 8}}>
              <QueryCountdown pollInterval={POLL_INTERVAL} queryResult={queryResult} />
            </Box>
          </Box>
        }
      />
      {selectedTab === 'queued' ? (
        <Group direction="column" spacing={8} padding={{horizontal: 24, vertical: 16}}>
          <Alert
            intent="info"
            title={<Link to="/instance/config#run_coordinator">View queue configuration</Link>}
          />
          <QueueDaemonAlert />
        </Group>
      ) : null}
      <RunsQueryRefetchContext.Provider value={{refetch: queryResult.refetch}}>
        <Loading queryResult={queryResult} allowStaleData={true}>
          {({pipelineRunsOrError}) => {
            if (pipelineRunsOrError.__typename !== 'PipelineRuns') {
              return (
                <Box padding={{vertical: 64}}>
                  <NonIdealState
                    icon="error"
                    title="Query Error"
                    description={pipelineRunsOrError.message}
                  />
                </Box>
              );
            }

            if (showScheduled) {
              return (
                <Box
                  padding={{vertical: 16}}
                  border={{side: 'top', width: 1, color: ColorsWIP.KeylineGray}}
                >
                  <AllScheduledTicks />
                </Box>
              );
            }

            return (
              <>
                <RunTable
                  runs={pipelineRunsOrError.results.slice(0, PAGE_SIZE)}
                  onSetFilter={setFilterTokens}
                  actionBarComponents={
                    showScheduled ? null : (
                      <RunsFilter
                        tokens={filterTokens}
                        onChange={setFilterTokens}
                        loading={queryResult.loading}
                        enabledFilters={enabledFilters}
                      />
                    )
                  }
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

  ${RUN_TABLE_RUN_FRAGMENT}
  ${COUNT_FRAGMENT}
`;

const QueueDaemonAlert = () => {
  const {data} = useQuery<QueueDaemonStatusQuery>(QUEUE_DAEMON_STATUS_QUERY);
  const status = data?.instance.daemonHealth.daemonStatus;
  if (status?.required && !status?.healthy) {
    return (
      <Alert
        intent="warning"
        title="The queued run coordinator is not healthy."
        description={
          <div>
            View <Link to="/instance/health">Instance status</Link> for details.
          </div>
        }
      />
    );
  }
  return null;
};

const QUEUE_DAEMON_STATUS_QUERY = gql`
  query QueueDaemonStatusQuery {
    instance {
      daemonHealth {
        id
        daemonStatus(daemonType: "QUEUED_RUN_COORDINATOR") {
          id
          daemonType
          healthy
          required
        }
      }
    }
  }
`;
