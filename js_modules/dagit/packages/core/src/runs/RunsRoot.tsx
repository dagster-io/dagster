import {gql, useQuery} from '@apollo/client';
import {Divider, NonIdealState, Tab, Tabs} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import isEqual from 'lodash/isEqual';
import * as React from 'react';
import {Link, RouteComponentProps} from 'react-router-dom';
import styled from 'styled-components/macro';

import {useFeatureFlags} from '../app/Flags';
import {QueryCountdown} from '../app/QueryCountdown';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {PipelineRunStatus} from '../types/globalTypes';
import {Alert} from '../ui/Alert';
import {Box} from '../ui/Box';
import {ButtonLink} from '../ui/ButtonLink';
import {ColorsWIP} from '../ui/Colors';
import {CursorPaginationControls} from '../ui/CursorControls';
import {Group} from '../ui/Group';
import {Loading} from '../ui/Loading';
import {Page} from '../ui/Page';
import {PageHeader} from '../ui/PageHeader';
import {TagWIP} from '../ui/TagWIP';
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
import {CountFragment} from './types/CountFragment';
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
  const {flagPipelineModeTuples} = useFeatureFlags();

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
  const tabColor = (match: string) =>
    selectedTab === match ? ColorsWIP.Link : {link: ColorsWIP.Gray500, hover: ColorsWIP.Link};
  const enabledFilters: RunFilterTokenType[] = flagPipelineModeTuples
    ? ['status', 'tag', 'snapshotId', 'id', 'job']
    : ['status', 'tag', 'snapshotId', 'id', 'pipeline'];

  return (
    <Page>
      <Group direction="column" spacing={8}>
        <Group direction="column" spacing={8} padding={{horizontal: 24}}>
          <PageHeader title={<Heading>Runs</Heading>} />
          <Box
            border={{side: 'bottom', width: 1, color: ColorsWIP.Gray100}}
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
                    <Group direction="row" spacing={4} alignItems="center">
                      <div>Queued</div>
                      <CountTag
                        loading={queryResult.loading && !queryResult.data}
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
                    <Group direction="row" spacing={4} alignItems="center">
                      <div>In progress</div>
                      <CountTag
                        loading={queryResult.loading && !queryResult.data}
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
              <div style={{display: 'flex', alignSelf: 'stretch'}}>
                <Divider style={{margin: '6px 0px'}} />
              </div>
              <Tab
                title={
                  <TabButton
                    color={tabColor('scheduled')}
                    underline="never"
                    onClick={() => setShowScheduled(true)}
                  >
                    Scheduled
                  </TabButton>
                }
                id="scheduled"
              />
            </Tabs>
            <Box padding={{bottom: 8}}>
              <QueryCountdown pollInterval={POLL_INTERVAL} queryResult={queryResult} />
            </Box>
          </Box>
          {showScheduled ? null : (
            <RunsFilter
              tokens={filterTokens}
              onChange={setFilterTokens}
              loading={queryResult.loading}
              enabledFilters={enabledFilters}
            />
          )}
          {selectedTab === 'queued' ? (
            <Group direction="column" spacing={8}>
              <Alert
                intent="info"
                title={<Link to="/instance/config#run_coordinator">View queue configuration</Link>}
              />
              <QueueDaemonAlert />
            </Group>
          ) : null}
        </Group>
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

              if (showScheduled) {
                return (
                  <Box margin={{top: 4}}>
                    <AllScheduledTicks />
                  </Box>
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
    return <TagWIP intent="none">–</TagWIP>;
  }
  if (typeof fragment?.count === 'number') {
    return <TagWIP intent="none">{fragment.count}</TagWIP>;
  }
  return null;
};
