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
  DialogBody,
} from '@dagster-io/ui';
import dayjs from 'dayjs';
import duration from 'dayjs/plugin/duration';
import relativeTime from 'dayjs/plugin/relativeTime';
import React from 'react';
import {Link, useParams} from 'react-router-dom';
import styled from 'styled-components/macro';

import {showCustomAlert} from '../../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../../app/PythonErrorFragment';
import {PythonErrorInfo} from '../../app/PythonErrorInfo';
import {QueryRefreshCountdown, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {useTrackPageView} from '../../app/analytics';
import {Timestamp} from '../../app/time/Timestamp';
import {assetDetailsPathForKey} from '../../assets/assetDetailsPathForKey';
import {BulkActionStatus, RunStatus} from '../../graphql/types';
import {useDocumentTitle} from '../../hooks/useDocumentTitle';
import {TruncatedTextWithFullTextOnHover} from '../../nav/getLeftNavItemsForOption';
import {RunFilterToken, runsPathWithFilters} from '../../runs/RunsFilterInput';
import {testId} from '../../testing/testId';
import {numberFormatter} from '../../ui/formatters';

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
    {
      variables: {backfillId},
    },
  );
  const {data} = queryResult;

  const backfill = data?.partitionBackfillOrError;
  let isInProgress = true;
  if (backfill && backfill.__typename === 'PartitionBackfill') {
    // for asset backfills, all of the requested runs have concluded in order for the status to be BulkActionStatus.COMPLETED
    isInProgress = backfill.status === BulkActionStatus.REQUESTED;
  }
  const refreshState = useQueryRefreshAtInterval(queryResult, 10000, isInProgress);

  function content() {
    if (!backfill || !data) {
      return (
        <Box padding={64} data-testid={testId('page-loading-indicator')}>
          <Spinner purpose="page" />
        </Box>
      );
    }
    if (backfill.__typename === 'PythonError') {
      return <PythonErrorInfo error={backfill} />;
    }

    function getRunsUrl(status: 'requested' | 'complete' | 'failed' | 'targeted') {
      const filters: RunFilterToken[] = [
        {
          token: 'tag',
          value: `dagster/backfill=${backfillId}`,
        },
      ];
      switch (status) {
        case 'requested':
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
            label="Partition Selection"
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
          <Detail label="Status" detail={<StatusLabel backfill={backfill} />} />
        </Box>
        <Table>
          <thead>
            <tr>
              <th style={{width: '50%'}}>Asset name</th>
              <th>
                <a href={getRunsUrl('targeted')}>Partitions targeted</a>
              </th>
              <th>
                <a href={getRunsUrl('requested')}>Requested</a>
              </th>
              <th>
                <a href={getRunsUrl('complete')}>Completed</a>
              </th>
              <th>
                <a href={getRunsUrl('failed')}>Failed</a>
              </th>
            </tr>
          </thead>
          <tbody>
            {backfill.assetBackfillData?.assetBackfillStatuses.map((asset) => {
              return asset.__typename === 'AssetPartitionsStatusCounts' ? (
                <tr key={asset.assetKey.path.join('/')}>
                  <td>
                    <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
                      <div>
                        <a href={assetDetailsPathForKey(asset.assetKey)}>
                          {asset.assetKey.path.join('/')}
                        </a>
                      </div>
                      <div>
                        <StatusBar
                          targeted={asset.numPartitionsTargeted}
                          requested={asset.numPartitionsInProgress}
                          completed={asset.numPartitionsMaterialized}
                          failed={asset.numPartitionsFailed}
                        />
                      </div>
                    </Box>
                  </td>
                  <td>{asset.numPartitionsTargeted}</td>
                  <td>{asset.numPartitionsInProgress}</td>
                  <td>{asset.numPartitionsMaterialized}</td>
                  <td>{asset.numPartitionsFailed}</td>
                </tr>
              ) : null;
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
          <div style={{fontSize: '18px'}}>
            <Link to="/overview/backfills" style={{color: Colors.Gray700}}>
              Backfills
            </Link>
            {' / '}
            {backfillId}
          </div>
        }
        right={isInProgress ? <QueryRefreshCountdown refreshState={refreshState} /> : null}
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

const StatusLabel = ({backfill}: {backfill: PartitionBackfillFragment}) => {
  switch (backfill.status) {
    case BulkActionStatus.REQUESTED:
      return <Tag>In Progress</Tag>;
    case BulkActionStatus.CANCELED:
    case BulkActionStatus.FAILED:
      if (backfill.error) {
        return (
          <Box margin={{bottom: 12}}>
            <TagButton
              onClick={() =>
                backfill.error &&
                showCustomAlert({title: 'Error', body: <PythonErrorInfo error={backfill.error} />})
              }
            >
              <Tag intent="danger">{backfill.status === 'FAILED' ? 'Failed' : 'Canceled'}</Tag>
            </TagButton>
          </Box>
        );
      }
      break;
    case BulkActionStatus.COMPLETED:
      return <Tag intent="success">Completed</Tag>;
  }
  return null;
};

function StatusBar({
  targeted,
  requested,
  completed,
  failed,
}: {
  targeted: number;
  requested: number;
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
          (100 * requested) / targeted
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
    }
  }

  fragment PartitionBackfillFragment on PartitionBackfill {
    id
    status
    timestamp
    endTimestamp
    numPartitions
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
      }
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;

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

  let dialogContent: JSX.Element | undefined;
  let content: JSX.Element | undefined;
  if (rootAssetTargetedPartitions) {
    if (rootAssetTargetedPartitions.length > 3) {
      dialogContent = (
        <div>
          {rootAssetTargetedPartitions.map((p) => (
            <div key={p} style={{maxWidth: '100px'}}>
              <TruncatedTextWithFullTextOnHover text={p} />
            </div>
          ))}
        </div>
      );
      content = (
        <ButtonLink
          onClick={() => {
            setIsDialogOpen(true);
          }}
        >
          {numberFormatter.format(numPartitions)} partitions
        </ButtonLink>
      );
    } else {
      content = (
        <Box flex={{direction: 'row', gap: 8, wrap: 'wrap'}}>
          {rootAssetTargetedPartitions.map((p) => (
            <div key={p}>{p}</div>
          ))}
        </Box>
      );
    }
  } else {
    if (rootAssetTargetedRanges?.length === 1) {
      const {start, end} = rootAssetTargetedRanges[0];
      content = (
        <div>
          {start}...{end}
        </div>
      );
    } else {
      content = (
        <ButtonLink
          onClick={() => {
            setIsDialogOpen(true);
          }}
        >
          {numberFormatter.format(numPartitions)} partitions
        </ButtonLink>
      );
      dialogContent = (
        <Box flex={{direction: 'column', gap: 8}}>
          {rootAssetTargetedRanges?.map((r) => (
            <div key={`${r.start}:${r.end}`}>
              {r.start}...{r.end}
            </div>
          ))}
        </Box>
      );
    }
  }

  return (
    <>
      <div>{content}</div>
      <Dialog isOpen={!!dialogContent && isDialogOpen} title="Partition selection">
        <DialogBody>{dialogContent}</DialogBody>
        <DialogFooter topBorder>
          <Button onClick={() => setIsDialogOpen(false)}>Close</Button>
        </DialogFooter>
      </Dialog>
    </>
  );
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

const TagButton = styled.button`
  border: none;
  background: none;
  cursor: pointer;
  padding: 0;
  margin: 0;

  :focus {
    outline: none;
  }
`;
