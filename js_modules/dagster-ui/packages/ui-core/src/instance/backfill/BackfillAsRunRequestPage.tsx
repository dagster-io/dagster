import {
  Alert,
  Box,
  Colors,
  Heading,
  NonIdealState,
  PageHeader,
  Spinner,
  Subtitle2,
  Tab,
  Tabs,
} from '@dagster-io/ui-components';
import {createContext, useContext} from 'react';
import {Link, useParams} from 'react-router-dom';

import {BackfillActionsMenu} from './BackfillActionsMenu';
import {BackfillLogsTab} from './BackfillLogsTab';
import {BackfillPartitionsTab} from './BackfillPartitionsTab';
import {BackfillRunsTab} from './BackfillRunsTab';
import {BackfillStatusTagForPage} from './BackfillStatusTagForPage';
import {LiveDuration} from './LiveDuration';
import {TargetPartitionsDisplay} from './TargetPartitionsDisplay';
import {useBackfillDetailsQuery} from './useBackfillDetailsQuery';
import {CloudOSSContext} from '../../app/CloudOSSContext';
import {PythonErrorInfo} from '../../app/PythonErrorInfo';
import {QueryRefreshCountdown, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {useTrackPageView} from '../../app/analytics';
import {Timestamp} from '../../app/time/Timestamp';
import {BulkActionStatus} from '../../graphql/types';
import {useDocumentTitle} from '../../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {
  DaemonNotRunningAlert,
  useIsBackfillDaemonHealthy,
} from '../../partitions/BackfillMessaging';
import {testId} from '../../testing/testId';

export const RunRequestContext = createContext<{
  buildLinkToRun: (run: {id: string}) => string;
}>({
  buildLinkToRun: ({id}) => `/runs/${id}`,
});

export const BackfillAsRunRequestPage = () => {
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
      <Box flex={{direction: 'row'}} style={{minHeight: 0, flex: 1}}>
        <Box style={{flex: 3, minHeight: 0}} flex={{direction: 'column'}}>
          <Box padding={{left: 24}} border="bottom">
            <Tabs size="large" selectedTabId={selectedTab}>
              <Tab id="runs" title="Runs" onClick={() => setSelectedTab('runs')} />
              <Tab
                id="partitions"
                title="Partitions"
                onClick={() => setSelectedTab('partitions')}
              />
              {featureContext.canSeeBackfillCoordinatorLogs ? (
                <Tab id="logs" title="Coordinator logs" onClick={() => setSelectedTab('logs')} />
              ) : null}
            </Tabs>
          </Box>
          {error?.graphQLErrors && (
            <Alert intent="error" title={error.graphQLErrors.map((err) => err.message)} />
          )}
          <RunRequestContext.Provider
            value={{buildLinkToRun: ({id}) => `/run-requests/b/${backfillId}/${id}`}}
          >
            <Box flex={{direction: 'column'}} style={{flex: 1, position: 'relative', minHeight: 0}}>
              {selectedTab === 'runs' && <BackfillRunsTab backfill={backfill} />}
              {selectedTab === 'partitions' && <BackfillPartitionsTab backfill={backfill} />}
              {selectedTab === 'logs' && <BackfillLogsTab backfill={backfill} />}
            </Box>
          </RunRequestContext.Provider>
        </Box>
        <Box style={{flex: 1, maxWidth: 400, minWidth: 250}} border="left">
          <Box
            padding={{horizontal: 24}}
            style={{height: 52}}
            flex={{alignItems: 'center'}}
            border="bottom"
          >
            <Subtitle2>Overview</Subtitle2>
          </Box>
          {isDaemonHealthy ? null : (
            <Box padding={{horizontal: 24, top: 16}}>
              <DaemonNotRunningAlert />
            </Box>
          )}

          <Box
            data-testid={testId('backfill-page-details')}
            padding={{horizontal: 24, vertical: 16}}
            flex={{
              direction: 'column',
              wrap: 'nowrap',
              gap: 12,
            }}
          >
            <Detail label="Status" detail={<BackfillStatusTagForPage backfill={backfill} />} />
            <Detail
              label="Created"
              detail={
                <Timestamp
                  timestamp={{ms: Number(backfill.timestamp * 1000)}}
                  timeFormat={{showSeconds: true, showTimezone: false}}
                />
              }
            />
            <Detail
              label="Duration"
              detail={
                <LiveDuration
                  start={backfill.timestamp * 1000}
                  end={backfill.endTimestamp ? backfill.endTimestamp * 1000 : null}
                />
              }
            />
            <Detail
              label="Partition selection"
              detail={
                <TargetPartitionsDisplay
                  targetPartitionCount={backfill.numPartitions || 0}
                  targetPartitions={backfill.assetBackfillData?.rootTargetedPartitions}
                />
              }
            />
          </Box>
        </Box>
      </Box>
    );
  }

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader
        title={
          <Heading>
            <Link to="/run-requests" style={{color: Colors.textLight()}}>
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

const Detail = ({label, detail}: {label: JSX.Element | string; detail: JSX.Element | string}) => (
  <Box flex={{direction: 'column', gap: 4}}>
    <Subtitle2>{label}</Subtitle2>
    <div>{detail}</div>
  </Box>
);
