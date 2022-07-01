import {ApolloError, gql, useQuery} from '@apollo/client';
import {
  Alert,
  Box,
  Colors,
  CursorHistoryControls,
  NonIdealState,
  Page,
  PageHeader,
  Tab,
  Tabs,
  Tag,
  Heading,
  TokenizingFieldValue,
  tokenToString,
} from '@dagster-io/ui';
import isEqual from 'lodash/isEqual';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useCanSeeConfig} from '../instance/useCanSeeConfig';
import {RunStatus} from '../types/globalTypes';
import {Loading} from '../ui/Loading';
import {StickyTableContainer} from '../ui/StickyTableContainer';

import {AllScheduledTicks} from './AllScheduledTicks';
import {doneStatuses, inProgressStatuses, queuedStatuses} from './RunStatuses';
import {RunTable, RUN_TABLE_RUN_FRAGMENT} from './RunTable';
import {RunsQueryRefetchContext} from './RunUtils';
import {
  RunFilterTokenType,
  RunsFilterInput,
  runsFilterForSearchTokens,
  useQueryPersistedRunFilters,
  RunFilterToken,
} from './RunsFilterInput';
import {QueueDaemonStatusQuery} from './types/QueueDaemonStatusQuery';
import {RunsRootQuery, RunsRootQueryVariables} from './types/RunsRootQuery';
import {useCursorPaginatedQuery} from './useCursorPaginatedQuery';

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

export const RunsRoot = () => {
  useDocumentTitle('Runs');
  const [filterTokens, setFilterTokens] = useQueryPersistedRunFilters();
  const filter = runsFilterForSearchTokens(filterTokens);
  const [showScheduled, setShowScheduled] = React.useState(false);
  const canSeeConfig = useCanSeeConfig();

  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    RunsRootQuery,
    RunsRootQueryVariables
  >({
    nextCursorForResult: (runs) => {
      if (runs.pipelineRunsOrError.__typename !== 'Runs') {
        return undefined;
      }
      return runs.pipelineRunsOrError.results[PAGE_SIZE - 1]?.runId;
    },
    getResultArray: (data) => {
      if (!data || data.pipelineRunsOrError.__typename !== 'Runs') {
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
  const refreshState = useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  const selectedTab = showScheduled ? 'scheduled' : selectedTabId(filterTokens);
  const staticStatusTags = selectedTab !== 'all';

  const setStatusFilter = (statuses: RunStatus[]) => {
    const tokensMinusStatus = filterTokens.filter((token) => token.token !== 'status');
    const statusTokens = statuses.map((status) => ({token: 'status' as const, value: status}));
    setFilterTokens([...statusTokens, ...tokensMinusStatus]);
    setShowScheduled(false);
  };

  const setFilterTokensWithStatus = React.useCallback(
    (tokens) => {
      if (staticStatusTags) {
        const statusTokens = filterTokens.filter((token) => token.token === 'status');
        setFilterTokens([...statusTokens, ...tokens]);
      } else {
        setFilterTokens(tokens);
      }
    },
    [filterTokens, setFilterTokens, staticStatusTags],
  );

  const onAddTag = React.useCallback(
    (token: RunFilterToken) => {
      const tokenAsString = tokenToString(token);
      if (!filterTokens.some((token) => tokenToString(token) === tokenAsString)) {
        setFilterTokensWithStatus([...filterTokens, token]);
      }
    },
    [filterTokens, setFilterTokensWithStatus],
  );

  const enabledFilters = React.useMemo(() => {
    const filters: RunFilterTokenType[] = ['tag', 'snapshotId', 'id', 'job', 'pipeline'];

    if (!staticStatusTags) {
      filters.push('status');
    }

    return filters;
  }, [staticStatusTags]);

  const mutableTokens = React.useMemo(() => {
    if (staticStatusTags) {
      return filterTokens.filter((token) => token.token !== 'status');
    }
    return filterTokens;
  }, [filterTokens, staticStatusTags]);

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
                  queryResult.data?.queuedCount?.__typename === 'Runs'
                    ? queryResult.data?.queuedCount.count
                    : 'indeterminate'
                }
                onClick={() => setStatusFilter(Array.from(queuedStatuses))}
                id="queued"
              />
              <Tab
                title="In progress"
                count={
                  queryResult.data?.inProgressCount?.__typename === 'Runs'
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
              <QueryRefreshCountdown refreshState={refreshState} />
            </Box>
          </Box>
        }
      />
      {selectedTab === 'queued' && canSeeConfig ? (
        <Box
          flex={{direction: 'column', gap: 8}}
          padding={{horizontal: 24, vertical: 16}}
          border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        >
          <Alert
            intent="info"
            title={<Link to="/instance/config#run_coordinator">View queue configuration</Link>}
          />
          <QueueDaemonAlert />
        </Box>
      ) : null}
      <RunsQueryRefetchContext.Provider value={{refetch: queryResult.refetch}}>
        <Loading
          queryResult={queryResult}
          allowStaleData
          renderError={(error: ApolloError) => {
            // In this case, a 400 is most likely due to invalid run filters, which are a GraphQL
            // validation error but surfaced as a 400.
            const badRequest = !!(
              error?.networkError &&
              'statusCode' in error.networkError &&
              error.networkError.statusCode === 400
            );
            return (
              <Box
                flex={{direction: 'column', gap: 32}}
                padding={{vertical: 8, left: 24, right: 12}}
              >
                <RunsFilterInput
                  tokens={mutableTokens}
                  onChange={setFilterTokensWithStatus}
                  loading={queryResult.loading}
                  enabledFilters={enabledFilters}
                />
                <NonIdealState
                  icon="warning"
                  title={badRequest ? 'Invalid run filters' : 'Unexpected error'}
                  description={
                    badRequest
                      ? 'The specified run filters are not valid. Please check the filters and try again.'
                      : 'An unexpected error occurred. Check the console for details.'
                  }
                />
              </Box>
            );
          }}
        >
          {({pipelineRunsOrError}) => {
            if (pipelineRunsOrError.__typename !== 'Runs') {
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
              return <AllScheduledTicks />;
            }

            return (
              <>
                <StickyTableContainer $top={0}>
                  <RunTable
                    runs={pipelineRunsOrError.results.slice(0, PAGE_SIZE)}
                    onAddTag={onAddTag}
                    filter={filter}
                    actionBarComponents={
                      showScheduled ? null : (
                        <Box flex={{direction: 'column', gap: 8}}>
                          {selectedTab !== 'all' ? (
                            <Box flex={{direction: 'row', gap: 8}}>
                              {filterTokens
                                .filter((token) => token.token === 'status')
                                .map(({token, value}) => (
                                  <Tag key={token}>{`${token}:${value}`}</Tag>
                                ))}
                            </Box>
                          ) : null}
                          <RunsFilterInput
                            tokens={mutableTokens}
                            onChange={setFilterTokensWithStatus}
                            loading={queryResult.loading}
                            enabledFilters={enabledFilters}
                          />
                        </Box>
                      )
                    }
                  />
                </StickyTableContainer>
                {pipelineRunsOrError.results.length > 0 ? (
                  <div style={{marginTop: '16px'}}>
                    <CursorHistoryControls {...paginationProps} />
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
  fragment CountFragment on Runs {
    count
  }
`;

const RUNS_ROOT_QUERY = gql`
  query RunsRootQuery(
    $limit: Int
    $cursor: String
    $filter: RunsFilter!
    $queuedFilter: RunsFilter!
    $inProgressFilter: RunsFilter!
  ) {
    pipelineRunsOrError(limit: $limit, cursor: $cursor, filter: $filter) {
      ... on Runs {
        results {
          id
          ...RunTableRunFragment
        }
      }
      ... on InvalidPipelineRunsFilterError {
        message
      }
      ...PythonErrorFragment
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
  ${PYTHON_ERROR_FRAGMENT}
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
