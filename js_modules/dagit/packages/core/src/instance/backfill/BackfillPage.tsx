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

import {PYTHON_ERROR_FRAGMENT} from '../../app/PythonErrorFragment';
import {PythonErrorInfo} from '../../app/PythonErrorInfo';
import {useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {useTrackPageView} from '../../app/analytics';
import {BulkActionStatus, RunStatus} from '../../graphql/types';
import {useDocumentTitle} from '../../hooks/useDocumentTitle';
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
  const {data, loading} = queryResult;

  const backfill = data?.partitionBackfillOrError;
  let isInProgress = true;
  if (backfill && backfill.__typename === 'PartitionBackfill') {
    isInProgress = backfill.status === BulkActionStatus.REQUESTED;
  }
  useQueryRefreshAtInterval(queryResult, 5000, isInProgress);

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
          <Detail label="Created" detail="Mar 22, 5:00 PM" />
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
          <Detail label="Status" detail={<StatusLabel status={backfill.status} />} />
        </Box>
        <Table>
          <thead>
            <tr>
              <th style={{width: '50%'}}>Asset name</th>
              <th>Partitions targeted</th>
              <th>Requested</th>
              <th>Complete</th>
              <th>Failed</th>
            </tr>
          </thead>
          <tbody>
            {backfill.assetBackfillData?.assetPartitionsStatusCounts.map((asset) => (
              <tr key={asset.assetKey.path.join('/')}>
                <td>
                  <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
                    <div>{asset.assetKey.path.join('/')}</div>
                    <div>
                      <StatusBar
                        targeted={asset.numPartitionsTargeted}
                        requested={asset.numPartitionsRequested}
                        completed={asset.numPartitionsCompleted}
                        failed={asset.numPartitionsFailed}
                      />
                    </div>
                  </Box>
                </td>
                <td>
                  <a href={getRunsUrl('targeted')}>{asset.numPartitionsTargeted}</a>
                </td>
                <td>
                  <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
                    <div>{asset.numPartitionsRequested}</div>
                    <div>
                      {asset.numPartitionsRequested ? (
                        <a href={getRunsUrl('requested')}>View Runs</a>
                      ) : null}
                    </div>
                  </Box>
                </td>
                <td>
                  <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
                    <div>{asset.numPartitionsCompleted}</div>
                    <div>
                      {asset.numPartitionsCompleted ? (
                        <a href={getRunsUrl('complete')}>View Runs</a>
                      ) : null}
                    </div>
                  </Box>
                </td>
                <td>
                  <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
                    <div>{asset.numPartitionsFailed}</div>
                    <div>
                      {asset.numPartitionsFailed ? (
                        <a href={getRunsUrl('failed')}>View Runs</a>
                      ) : null}
                    </div>
                  </Box>
                </td>
              </tr>
            ))}
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

const StatusLabel = ({status}: {status: BulkActionStatus}) => {
  switch (status) {
    case BulkActionStatus.CANCELED:
      return <Tag intent="warning">Canceled</Tag>;
    case BulkActionStatus.COMPLETED:
      return <Tag intent="success">Complete</Tag>;
    case BulkActionStatus.FAILED:
      return <Tag intent="danger">Failed</Tag>;
    case BulkActionStatus.REQUESTED:
      return (
        <Tag intent="primary" icon="spinner">
          In Progress
        </Tag>
      );
    default:
      return <Tag intent="warning">Incomplete</Tag>;
  }
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

  const str = dayjs.duration(duration).humanize(false);
  return <span>{str}</span>;
};

export const BACKFILL_DETAILS_QUERY = gql`
  query BackfillStatusesByAsset($backfillId: String!) {
    partitionBackfillOrError(backfillId: $backfillId) {
      ...PartitionBackfillFragment
      ...PythonErrorFragment
    }
  }

  fragment PartitionBackfillFragment on PartitionBackfill {
    status
    timestamp
    endTimestamp
    numPartitions
    assetBackfillData {
      rootAssetTargetedRanges {
        start
        end
      }
      rootAssetTargetedPartitions
      assetPartitionsStatusCounts {
        assetKey {
          path
        }
        numPartitionsTargeted
        numPartitionsRequested
        numPartitionsCompleted
        numPartitionsFailed
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
            <div key={p}>{p}</div>
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
          {start} - {end}
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
              {r.start} - {r.end}
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
