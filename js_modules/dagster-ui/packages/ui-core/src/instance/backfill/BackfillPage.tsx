import {gql, useQuery} from '@apollo/client';
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
import dayjs from 'dayjs';
import duration from 'dayjs/plugin/duration';
import relativeTime from 'dayjs/plugin/relativeTime';
import {useContext, useEffect, useReducer} from 'react';
import {Link, useParams} from 'react-router-dom';
import styled from 'styled-components';

import {BACKFILL_ACTIONS_BACKFILL_FRAGMENT, BackfillActionsMenu} from './BackfillActionsMenu';
import {BackfillLogsTab} from './BackfillLogsTab';
import {BackfillPartitionsTab} from './BackfillPartitionsTab';
import {BackfillRunsTab} from './BackfillRunsTab';
import {BackfillStatusTagForPage} from './BackfillStatusTagForPage';
import {TargetPartitionsDisplay} from './TargetPartitionsDisplay';
import {
  BackfillStatusesByAssetQuery,
  BackfillStatusesByAssetQueryVariables,
} from './types/BackfillPage.types';
import {CloudOSSContext} from '../../app/CloudOSSContext';
import {PYTHON_ERROR_FRAGMENT} from '../../app/PythonErrorFragment';
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
import {useBlockTraceOnQueryResult} from '../../performance/TraceContext';
import {testId} from '../../testing/testId';

dayjs.extend(duration);
dayjs.extend(relativeTime);

export const BackfillPage = () => {
  const {featureContext} = useContext(CloudOSSContext);
  const {backfillId} = useParams<{backfillId: string}>();
  useTrackPageView();
  useDocumentTitle(`Backfill | ${backfillId}`);

  const [selectedTab, setSelectedTab] = useQueryPersistedState<'partitions' | 'logs' | 'runs'>({
    queryKey: 'tab',
    defaults: {tab: 'partitions'},
  });

  const isDaemonHealthy = useIsBackfillDaemonHealthy();

  const queryResult = useQuery<BackfillStatusesByAssetQuery, BackfillStatusesByAssetQueryVariables>(
    BACKFILL_DETAILS_QUERY,
    {variables: {backfillId}},
  );
  useBlockTraceOnQueryResult(queryResult, 'BackfillStatusesByAssetQuery');

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
        <Box
          padding={24}
          flex={{
            direction: 'row',
            justifyContent: 'space-between',
            wrap: 'nowrap',
            alignItems: 'center',
          }}
          data-testid={testId('backfill-page-details')}
        >
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
              <BackfillDuration
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
          <Detail label="Status" detail={<BackfillStatusTagForPage backfill={backfill} />} />
        </Box>

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
          {selectedTab === 'partitions' && <BackfillPartitionsTab backfill={backfill} />}
          {selectedTab === 'runs' && <BackfillRunsTab backfill={backfill} />}
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

const Detail = ({label, detail}: {label: JSX.Element | string; detail: JSX.Element | string}) => (
  <Box flex={{direction: 'column', gap: 4}} style={{minWidth: '280px'}}>
    <Label>{label}</Label>
    <div>{detail}</div>
  </Box>
);

const Label = styled.div`
  color: ${Colors.textLight()};
  font-size: 12px;
  line-height: 16px;
`;

const BackfillDuration = ({start, end}: {start: number; end?: number | null}) => {
  const [_, rerender] = useReducer((s: number, _: any) => s + 1, 0);
  useEffect(() => {
    if (end) {
      return;
    }
    const intervalId = setInterval(rerender, 1000);
    return () => clearInterval(intervalId);
  }, [start, end]);
  const duration = end ? end - start : Date.now() - start;

  return <span>{formatDuration(duration)}</span>;
};

export const BACKFILL_DETAILS_QUERY = gql`
  query BackfillStatusesByAsset($backfillId: String!) {
    partitionBackfillOrError(backfillId: $backfillId) {
      ...BackfillDetailsBackfillFragment
      ...PythonErrorFragment
      ... on BackfillNotFoundError {
        message
      }
    }
  }

  fragment BackfillDetailsBackfillFragment on PartitionBackfill {
    id
    status
    timestamp
    endTimestamp
    numPartitions
    ...BackfillActionsBackfillFragment

    error {
      ...PythonErrorFragment
    }
    assetBackfillData {
      rootTargetedPartitions {
        partitionKeys
        ranges {
          start
          end
        }
      }
      assetBackfillStatuses {
        ... on AssetPartitionsStatusCounts {
          assetKey {
            path
          }
          numPartitionsTargeted
          numPartitionsInProgress
          numPartitionsMaterialized
          numPartitionsFailed
        }
        ... on UnpartitionedAssetStatus {
          assetKey {
            path
          }
          inProgress
          materialized
          failed
        }
      }
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
  ${BACKFILL_ACTIONS_BACKFILL_FRAGMENT}
`;

export const BACKFILL_PARTITIONS_FOR_ASSET_KEY_QUERY = gql`
  query BackfillPartitionsForAssetKey($backfillId: String!, $assetKey: AssetKeyInput!) {
    partitionBackfillOrError(backfillId: $backfillId) {
      ... on PartitionBackfill {
        id
        partitionsTargetedForAssetKey(assetKey: $assetKey) {
          partitionKeys
          ranges {
            start
            end
          }
        }
      }
    }
  }
`;

const formatDuration = (duration: number) => {
  const seconds = Math.floor((duration / 1000) % 60);
  const minutes = Math.floor((duration / (1000 * 60)) % 60);
  const hours = Math.floor((duration / (1000 * 60 * 60)) % 24);
  const days = Math.floor(duration / (1000 * 60 * 60 * 24));

  let result = '';
  if (days > 0) {
    result += `${days}d `;
    result += `${hours}h`;
  } else if (hours > 0) {
    result += `${hours}h `;
    result += `${minutes}m`;
  } else if (minutes > 0) {
    result += `${minutes}m `;
    result += `${seconds}s`;
  } else if (seconds > 0) {
    result += `${seconds}s`;
  }
  return result.trim();
};
