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
import {testId} from '../../testing/testId';

export const BackfillPage = () => {
  const {featureContext} = useContext(CloudOSSContext);
  const {backfillId} = useParams<{backfillId: string}>();
  useTrackPageView();
  useDocumentTitle(`Backfill | ${backfillId}`);

  const [selectedTab, setSelectedTab] = useQueryPersistedState<'partitions' | 'logs' | 'runs'>({
    queryKey: 'tab',
    defaults: {tab: 'partitions'},
  });

  const queryResult = useBackfillDetailsQuery(backfillId);
  const isDaemonHealthy = useIsBackfillDaemonHealthy();
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
      <>
        <BackfillOverviewDetails backfill={backfill} />

        {isDaemonHealthy ? null : (
          <Box padding={{horizontal: 24, bottom: 16}}>
            <DaemonNotRunningAlert />
          </Box>
        )}

        <Box padding={{left: 24}} border="bottom">
          <Tabs size="large" selectedTabId={selectedTab}>
            <Tab id="partitions" title="Partitions" onClick={() => setSelectedTab('partitions')} />
            <Tab id="runs" title="Runs" onClick={() => setSelectedTab('runs')} />
            {featureContext.canSeeBackfillCoordinatorLogs ? (
              <Tab id="logs" title="Coordinator logs" onClick={() => setSelectedTab('logs')} />
            ) : null}
          </Tabs>
        </Box>

        {error?.graphQLErrors && (
          <Alert intent="error" title={error.graphQLErrors.map((err) => err.message)} />
        )}
        <Box flex={{direction: 'column'}} style={{flex: 1, position: 'relative', minHeight: 0}}>
          {selectedTab === 'partitions' && <BackfillAssetPartitionsTable backfill={backfill} />}
          {selectedTab === 'runs' && <BackfillRunsTab backfill={backfill} view="both" />}
          {selectedTab === 'logs' && <BackfillLogsTab backfill={backfill} />}
        </Box>
      </>
    );
  }

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader
        title={
          <Heading>
            <Link to="/overview/backfills" style={{color: Colors.textLight()}}>
              Backfills
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
