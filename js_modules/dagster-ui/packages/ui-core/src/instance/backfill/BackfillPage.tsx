import {gql, useQuery} from '@apollo/client';
import {
  Page,
  PageHeader,
  Colors,
  Box,
  Tag,
  Table,
  Spinner,
  Dialog,
  Button,
  DialogFooter,
  ButtonLink,
  NonIdealState,
  Heading,
} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import duration from 'dayjs/plugin/duration';
import relativeTime from 'dayjs/plugin/relativeTime';
import React from 'react';
import {Link, useParams} from 'react-router-dom';
import styled from 'styled-components';

import {PYTHON_ERROR_FRAGMENT} from '../../app/PythonErrorFragment';
import {PythonErrorInfo} from '../../app/PythonErrorInfo';
import {QueryRefreshCountdown, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {useTrackPageView} from '../../app/analytics';
import {Timestamp} from '../../app/time/Timestamp';
import {tokenForAssetKey} from '../../asset-graph/Utils';
import {assetDetailsPathForKey} from '../../assets/assetDetailsPathForKey';
import {BulkActionStatus, RunStatus} from '../../graphql/types';
import {useDocumentTitle} from '../../hooks/useDocumentTitle';
import {TruncatedTextWithFullTextOnHover} from '../../nav/getLeftNavItemsForOption';
import {RunFilterToken, runsPathWithFilters} from '../../runs/RunsFilterInput';
import {testId} from '../../testing/testId';
import {VirtualizedItemListForDialog} from '../../ui/VirtualizedItemListForDialog';
import {numberFormatter} from '../../ui/formatters';

import {BACKFILL_ACTIONS_BACKFILL_FRAGMENT, BackfillActionsMenu} from './BackfillActionsMenu';
import {BackfillStatusTagForPage} from './BackfillStatusTagForPage';
import {
  BackfillStatusesByAssetQuery,
  BackfillStatusesByAssetQueryVariables,
  PartitionBackfillFragment,
} from './types/BackfillPage.types';

dayjs.extend(duration);
dayjs.extend(relativeTime);

export const BackfillPage = () => {
  const {backfillId} = useParams<{backfillId: string}>();
  useTrackPageView();
  useDocumentTitle(`Backfill | ${backfillId}`);

  const queryResult = useQuery<BackfillStatusesByAssetQuery, BackfillStatusesByAssetQueryVariables>(
    BACKFILL_DETAILS_QUERY,
    {variables: {backfillId}},
  );

  const {data} = queryResult;

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

    function getRunsUrl(status: 'inProgress' | 'complete' | 'failed' | 'targeted') {
      const filters: RunFilterToken[] = [
        {
          token: 'tag',
          value: `dagster/backfill=${backfillId}`,
        },
      ];
      switch (status) {
        case 'inProgress':
          filters.push(
            {
              token: 'status',
              value: RunStatus.STARTED,
            },
            {
              token: 'status',
              value: RunStatus.QUEUED,
            },
            {
              token: 'status',
              value: RunStatus.STARTING,
            },
            {
              token: 'status',
              value: RunStatus.CANCELING,
            },
            {
              token: 'status',
              value: RunStatus.NOT_STARTED,
            },
          );
          break;
        case 'complete':
          filters.push({
            token: 'status',
            value: RunStatus.SUCCESS,
          });
          break;
        case 'failed':
          filters.push({
            token: 'status',
            value: RunStatus.FAILURE,
          });
          filters.push({
            token: 'status',
            value: RunStatus.CANCELED,
          });
          break;
      }
      return runsPathWithFilters(filters);
    }

    const linkQuery = () => {
      if (backfill.assetBackfillData?.rootAssetTargetedRanges?.length === 1) {
        const ranges = backfill.assetBackfillData?.rootAssetTargetedRanges;
        if (ranges?.length) {
          const {start, end} = ranges[0]!;
          return {default_range: `[${start}...${end}]`};
        }
      }
      return undefined;
    };

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
              <Duration
                start={backfill.timestamp * 1000}
                end={backfill.endTimestamp ? backfill.endTimestamp * 1000 : null}
              />
            }
          />
          <Detail
            label="Partition selection"
            detail={
              <PartitionSelection
                numPartitions={backfill.numPartitions || 0}
                rootAssetTargetedPartitions={
                  backfill.assetBackfillData?.rootAssetTargetedPartitions
                }
                rootAssetTargetedRanges={backfill.assetBackfillData?.rootAssetTargetedRanges}
              />
            }
          />
          <Detail label="Status" detail={<BackfillStatusTagForPage backfill={backfill} />} />
        </Box>
        <Table>
          <thead>
            <tr>
              <th style={{width: '50%'}}>Asset name</th>
              <th>
                <Link to={getRunsUrl('targeted')}>Partitions targeted</Link>
              </th>
              <th>
                <Link to={getRunsUrl('inProgress')}>In progress</Link>
              </th>
              <th>
                <Link to={getRunsUrl('complete')}>Completed</Link>
              </th>
              <th>
                <Link to={getRunsUrl('failed')}>Failed</Link>
              </th>
            </tr>
          </thead>
          <tbody>
            {backfill.assetBackfillData?.assetBackfillStatuses.map((asset) => {
              let targeted;
              let inProgress;
              let completed;
              let failed;
              if (asset.__typename === 'AssetPartitionsStatusCounts') {
                targeted = asset.numPartitionsTargeted;
                inProgress = asset.numPartitionsInProgress;
                completed = asset.numPartitionsMaterialized;
                failed = asset.numPartitionsFailed;
              } else {
                targeted = 1;
                failed = asset.failed ? 1 : 0;
                inProgress = asset.inProgress ? 1 : 0;
                completed = asset.materialized ? 1 : 0;
              }
              return (
                <tr
                  key={tokenForAssetKey(asset.assetKey)}
                  data-testid={testId(`backfill-asset-row-${tokenForAssetKey(asset.assetKey)}`)}
                >
                  <td>
                    <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
                      <div>
                        <Link to={assetDetailsPathForKey(asset.assetKey, linkQuery())}>
                          {asset.assetKey.path.join('/')}
                        </Link>
                      </div>
                      <div>
                        <StatusBar
                          targeted={targeted}
                          inProgress={inProgress}
                          completed={completed}
                          failed={failed}
                        />
                      </div>
                    </Box>
                  </td>
                  {asset.__typename === 'AssetPartitionsStatusCounts' ? (
                    <>
                      <td>{targeted}</td>
                      <td>{inProgress}</td>
                      <td>{completed}</td>
                      <td>{failed}</td>
                    </>
                  ) : (
                    <>
                      <td>-</td>
                      <td>
                        {inProgress ? (
                          <Tag icon="spinner" intent="primary">
                            In progress
                          </Tag>
                        ) : (
                          '-'
                        )}
                      </td>
                      <td>{completed ? <Tag intent="success">Completed</Tag> : '-'}</td>
                      <td>{failed ? <Tag intent="danger">Failed</Tag> : '-'}</td>
                    </>
                  )}
                </tr>
              );
            })}
          </tbody>
        </Table>
      </>
    );
  }

  return (
    <Page>
      <PageHeader
        title={
          <Heading>
            <Link to="/overview/backfills" style={{color: Colors.Gray700}}>
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
    </Page>
  );
};

const Detail = ({label, detail}: {label: JSX.Element | string; detail: JSX.Element | string}) => (
  <Box flex={{direction: 'column', gap: 4}} style={{minWidth: '280px'}}>
    <Label>{label}</Label>
    <div>{detail}</div>
  </Box>
);

function StatusBar({
  targeted,
  inProgress,
  completed,
  failed,
}: {
  targeted: number;
  inProgress: number;
  completed: number;
  failed: number;
}) {
  return (
    <div
      style={{
        borderRadius: '8px',
        backgroundColor: Colors.Gray100,
        display: 'grid',
        gridTemplateColumns: `${(100 * completed) / targeted}% ${(100 * failed) / targeted}% ${
          (100 * inProgress) / targeted
        }%`,
        gridTemplateRows: '100%',
        height: '12px',
        width: '200px',
        overflow: 'hidden',
      }}
    >
      <div style={{background: Colors.Green500}} />
      <div style={{background: Colors.Red500}} />
      <div style={{background: Colors.Blue200}} />
    </div>
  );
}

const Label = styled.div`
  color: ${Colors.Gray700};
  font-size: 12px;
  line-height: 16px;
`;

const Duration = ({start, end}: {start: number; end?: number | null}) => {
  const [_, rerender] = React.useReducer((s: number, _: any) => s + 1, 0);
  React.useEffect(() => {
    if (end) {
      return;
    }
    // re-render once a minute to update the "time ago"
    const intervalId = setInterval(rerender, 60000);
    return () => clearInterval(intervalId);
  }, [start, end]);
  const duration = end ? end - start : Date.now() - start;

  return <span>{formatDuration(duration)}</span>;
};

export const BACKFILL_DETAILS_QUERY = gql`
  query BackfillStatusesByAsset($backfillId: String!) {
    partitionBackfillOrError(backfillId: $backfillId) {
      ...PartitionBackfillFragment
      ...PythonErrorFragment
      ... on BackfillNotFoundError {
        message
      }
    }
  }

  fragment PartitionBackfillFragment on PartitionBackfill {
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
      rootAssetTargetedRanges {
        start
        end
      }
      rootAssetTargetedPartitions
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

const COLLATOR = new Intl.Collator(navigator.language, {sensitivity: 'base', numeric: true});

type AssetBackfillData = Extract<
  PartitionBackfillFragment['assetBackfillData'],
  {__typename: 'AssetBackfillData'}
>;

export const PartitionSelection = ({
  numPartitions,
  rootAssetTargetedRanges,
  rootAssetTargetedPartitions,
}: {
  numPartitions: number;
  rootAssetTargetedRanges?: AssetBackfillData['rootAssetTargetedRanges'];
  rootAssetTargetedPartitions?: AssetBackfillData['rootAssetTargetedPartitions'];
}) => {
  const [isDialogOpen, setIsDialogOpen] = React.useState(false);

  if (rootAssetTargetedPartitions) {
    if (rootAssetTargetedPartitions.length <= 3) {
      return (
        <Box flex={{direction: 'row', gap: 8, wrap: 'wrap'}}>
          {rootAssetTargetedPartitions.map((p) => (
            <Tag key={p}>{p}</Tag>
          ))}
        </Box>
      );
    }

    return (
      <>
        <ButtonLink onClick={() => setIsDialogOpen(true)}>
          {numberFormatter.format(numPartitions)} partitions
        </ButtonLink>
        <Dialog
          isOpen={isDialogOpen}
          title={`Partition selection (${rootAssetTargetedPartitions.length})`}
          onClose={() => setIsDialogOpen(false)}
        >
          <div style={{height: '340px', overflow: 'hidden'}}>
            <VirtualizedItemListForDialog
              items={[...rootAssetTargetedPartitions].sort((a, b) => COLLATOR.compare(a, b))}
              renderItem={(assetKey) => (
                <div key={assetKey}>
                  <TruncatedTextWithFullTextOnHover text={assetKey} />
                </div>
              )}
            />
          </div>
          <DialogFooter topBorder>
            <Button onClick={() => setIsDialogOpen(false)}>Close</Button>
          </DialogFooter>
        </Dialog>
      </>
    );
  }

  if (rootAssetTargetedRanges) {
    if (rootAssetTargetedRanges?.length === 1) {
      const {start, end} = rootAssetTargetedRanges[0]!;
      return (
        <div>
          {start}...{end}
        </div>
      );
    }

    return (
      <>
        <ButtonLink onClick={() => setIsDialogOpen(true)}>
          {numberFormatter.format(numPartitions)} partitions
        </ButtonLink>
        <Dialog
          isOpen={isDialogOpen}
          title={`Partition selection (${rootAssetTargetedRanges?.length})`}
          onClose={() => setIsDialogOpen(false)}
        >
          <div style={{height: '340px', overflow: 'hidden'}}>
            <VirtualizedItemListForDialog
              items={rootAssetTargetedRanges || []}
              renderItem={({start, end}) => {
                return <div key={`${start}:${end}`}>{`${start}...${end}`}</div>;
              }}
            />
          </div>
          <DialogFooter topBorder>
            <Button onClick={() => setIsDialogOpen(false)}>Close</Button>
          </DialogFooter>
        </Dialog>
      </>
    );
  }

  return <div>{numPartitions === 1 ? '1 partition' : `${numPartitions} partitions`}</div>;
};

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
  }
  return result.trim();
};
