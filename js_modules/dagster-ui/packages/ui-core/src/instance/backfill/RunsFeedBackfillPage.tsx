import {
  Alert,
  Box,
  Colors,
  Heading,
  NonIdealState,
  PageHeader,
  Spinner,
  Tab,
  Tabs,
} from '@dagster-io/ui-components';
import {useContext} from 'react';
import {Link, useParams} from 'react-router-dom';

import {BackfillActionsMenu} from './BackfillActionsMenu';
import {BackfillAssetPartitionsTable} from './BackfillAssetPartitionsTable';
import {BackfillLogsTab} from './BackfillLogsTab';
import {BackfillOpJobPartitionsTable} from './BackfillOpJobPartitionsTable';
import {BackfillOverviewDetails} from './BackfillOverviewDetails';
import {BackfillRunsTab} from './BackfillRunsTab';
import {useBackfillDetailsQuery} from './useBackfillDetailsQuery';
import {CloudOSSContext} from '../../app/CloudOSSContext';
import {PythonErrorInfo} from '../../app/PythonErrorInfo';
import {QueryRefreshCountdown, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {useTrackPageView} from '../../app/analytics';
import {BulkActionStatus} from '../../graphql/types';
import {useDocumentTitle} from '../../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {
  DaemonNotRunningAlert,
  useIsBackfillDaemonHealthy,
} from '../../partitions/BackfillMessaging';
import {getRunFeedPath} from '../../runs/RunsFeedUtils';
import {testId} from '../../testing/testId';

export const RunsFeedBackfillPage = () => {
  const {featureContext} = useContext(CloudOSSContext);
  const {backfillId} = useParams<{backfillId: string}>();
  useTrackPageView();
  useDocumentTitle(`Backfill | ${backfillId}`);

  const isDaemonHealthy = useIsBackfillDaemonHealthy();

  const [selectedTab, setSelectedTab] = useQueryPersistedState<
    'overview' | 'logs' | 'runs' | 'timeline'
  >({
    queryKey: 'tab',
    defaults: {tab: 'overview'},
  });

  const queryResult = useBackfillDetailsQuery(backfillId);
  const {data, error} = queryResult;

  const backfill =
    data?.partitionBackfillOrError.__typename === 'PartitionBackfill'
      ? data.partitionBackfillOrError
      : null;

  // for asset backfills, all of the requested runs have concluded in order for the status to be BulkActionStatus.COMPLETED
  const isInProgress = backfill
    ? [BulkActionStatus.REQUESTED, BulkActionStatus.CANCELING].includes(backfill.status)
    : true;

  const refreshState = useQueryRefreshAtInterval(queryResult, 10000, isInProgress);

  function content() {
    if (!data || !data.partitionBackfillOrError) {
      return (
        <Box padding={64} data-testid={testId('page-loading-indicator')}>
          <Spinner purpose="page" />
        </Box>
      );
    }
    if (data.partitionBackfillOrError.__typename === 'PythonError') {
      return <PythonErrorInfo error={data.partitionBackfillOrError} />;
    }
    if (data.partitionBackfillOrError.__typename === 'BackfillNotFoundError') {
      return <NonIdealState icon="no-results" title={data.partitionBackfillOrError.message} />;
    }

    const backfill = data.partitionBackfillOrError;

    return (
      <Box style={{flex: 3, minHeight: 0}} flex={{direction: 'column'}}>
        <Box padding={{left: 24}} border="bottom">
          <Tabs size="large" selectedTabId={selectedTab}>
            <Tab id="overview" title="Overview" onClick={() => setSelectedTab('overview')} />
            <Tab id="runs" title="Runs" onClick={() => setSelectedTab('runs')} />
            <Tab id="timeline" title="Timeline" onClick={() => setSelectedTab('timeline')} />
            {featureContext.canSeeBackfillCoordinatorLogs ? (
              <Tab id="logs" title="Coordinator logs" onClick={() => setSelectedTab('logs')} />
            ) : null}
          </Tabs>
        </Box>
        {error?.graphQLErrors && (
          <Alert intent="error" title={error.graphQLErrors.map((err) => err.message)} />
        )}
        <Box flex={{direction: 'column'}} style={{flex: 1, position: 'relative', minHeight: 0}}>
          {selectedTab === 'overview' && (
            <Box style={{overflow: 'hidden'}} flex={{direction: 'column'}}>
              {isDaemonHealthy ? null : (
                <Box padding={{horizontal: 24, top: 16}}>
                  <DaemonNotRunningAlert />
                </Box>
              )}

              <BackfillOverviewDetails backfill={backfill} />
              {backfill.isAssetBackfill ? (
                <BackfillAssetPartitionsTable backfill={backfill} />
              ) : (
                <BackfillOpJobPartitionsTable backfill={backfill} />
              )}
            </Box>
          )}
          {selectedTab === 'runs' && <BackfillRunsTab backfill={backfill} view="list" />}
          {selectedTab === 'timeline' && <BackfillRunsTab backfill={backfill} view="timeline" />}
          {selectedTab === 'logs' && <BackfillLogsTab backfill={backfill} />}
        </Box>
      </Box>
    );
  }

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader
        title={
          <Heading>
            <Link to={getRunFeedPath()} style={{color: Colors.textLight()}}>
              All runs
            </Link>
            {' / '}
            {backfillId}
          </Heading>
        }
        right={
          <Box flex={{gap: 12, alignItems: 'center'}}>
            {isInProgress ? <QueryRefreshCountdown refreshState={refreshState} /> : null}
            {backfill ? (
              <BackfillActionsMenu
                backfill={backfill}
                refetch={queryResult.refetch}
                canCancelRuns={backfill.status === BulkActionStatus.REQUESTED}
              />
            ) : null}
          </Box>
        }
      />
      {content()}
    </Box>
  );
};
