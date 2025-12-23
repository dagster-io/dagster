import {Box, Caption, Colors, MiddleTruncate, NonIdealState, Tag} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {useRef} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {BackfillDetailsBackfillFragment} from './types/useBackfillDetailsQuery.types';
import {gql} from '../../apollo-client';
import {displayNameForAssetKey, tokenForAssetKey} from '../../asset-graph/Utils';
import {assetDetailsPathForKey} from '../../assets/assetDetailsPathForKey';
import {
  failedStatuses,
  inProgressStatuses,
  queuedStatuses,
  successStatuses,
} from '../../runs/RunStatuses';
import {RunFilterToken, runsPathWithFilters} from '../../runs/RunsFilterInput';
import {testId} from '../../testing/testId';
import {Container, HeaderCell, HeaderRow, Inner, Row, RowCell} from '../../ui/VirtualizedTable';
import {numberFormatter} from '../../ui/formatters';

const TEMPLATE_COLUMNS = '60% repeat(4, 1fr)';

type AssetBackfillStatus = NonNullable<
  BackfillDetailsBackfillFragment['assetBackfillData']
>['assetBackfillStatuses'][0];

export const BackfillAssetPartitionsTable = ({
  backfill,
}: {
  backfill: BackfillDetailsBackfillFragment;
}) => {
  const parentRef = useRef<HTMLDivElement | null>(null);

  const assetStatuses: AssetBackfillStatus[] =
    backfill.assetBackfillData?.assetBackfillStatuses ?? [];

  const rowVirtualizer = useVirtualizer({
    count: assetStatuses.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 64,
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  if (!assetStatuses.length) {
    return (
      <Box margin={48}>
        <NonIdealState
          title="Partition statuses unavailable"
          description="Dagster was unable to load per-partition statuses. This may occur if the backfilled assets or jobs no longer exist in your loaded code locations."
        />
      </Box>
    );
  }
  return (
    <Container ref={parentRef}>
      <VirtualizedBackfillPartitionsHeader backfill={backfill} />
      <Inner $totalHeight={totalHeight}>
        {items.map(({index, key, size, start}) => (
          <VirtualizedBackfillPartitionsRow
            key={key}
            // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
            asset={assetStatuses[index]!}
            height={size}
            start={start}
          />
        ))}
      </Inner>
    </Container>
  );
};

function getRunsUrl(
  backfillId: string,
  status: 'inProgress' | 'succeeded' | 'failed' | 'targeted',
) {
  const filters: RunFilterToken[] = [];

  switch (status) {
    /** Note: We don't include "Queued" runs on the "In progress" tab
     * of the runs page because there's a separate Queued tab. However,
     * they are included in the `assetBackfillStatuses.inProgress`, so we
     * need both filters here so that WYSIWYG when you click the link.
     */
    case 'inProgress':
      filters.push(
        ...Array.from(inProgressStatuses).map((value) => ({
          token: 'status' as const,
          value,
        })),
        ...Array.from(queuedStatuses).map((value) => ({
          token: 'status' as const,
          value,
        })),
      );
      break;
    case 'succeeded':
      filters.push(
        ...Array.from(successStatuses).map((value) => ({
          token: 'status' as const,
          value,
        })),
      );
      break;
    case 'failed':
      filters.push(
        ...Array.from(failedStatuses).map((value) => ({
          token: 'status' as const,
          value,
        })),
      );
      break;
  }
  return `/runs/b/${backfillId}/${runsPathWithFilters(filters, ``)}&tab=runs`;
}

export const VirtualizedBackfillPartitionsHeader = ({
  backfill,
}: {
  backfill: BackfillDetailsBackfillFragment;
}) => {
  return (
    <HeaderRow templateColumns={TEMPLATE_COLUMNS} sticky>
      <HeaderCell>Asset name</HeaderCell>
      <HeaderCell>
        <Link to={getRunsUrl(backfill.id, 'targeted')}>Partitions targeted</Link>
      </HeaderCell>
      <HeaderCell>
        <Link to={getRunsUrl(backfill.id, 'inProgress')}>In progress</Link>
      </HeaderCell>
      <HeaderCell>
        <Link to={getRunsUrl(backfill.id, 'succeeded')}>Succeeded</Link>
      </HeaderCell>
      <HeaderCell>
        <Link to={getRunsUrl(backfill.id, 'failed')}>Failed</Link>
      </HeaderCell>
    </HeaderRow>
  );
};

export const VirtualizedBackfillPartitionsRow = ({
  asset,
  height,
  start,
}: {
  asset: AssetBackfillStatus;
  height: number;
  start: number;
}) => {
  let targeted;
  let inProgress;
  let succeeded;
  let failed;
  if (asset.__typename === 'AssetPartitionsStatusCounts') {
    targeted = asset.numPartitionsTargeted;
    inProgress = asset.numPartitionsInProgress;
    succeeded = asset.numPartitionsMaterialized;
    failed = asset.numPartitionsFailed;
  } else {
    targeted = 1;
    failed = asset.failed ? 1 : 0;
    inProgress = asset.inProgress ? 1 : 0;
    succeeded = asset.materialized ? 1 : 0;
  }

  return (
    <Row
      $height={height}
      $start={start}
      data-testid={testId(`backfill-asset-row-${tokenForAssetKey(asset.assetKey)}`)}
    >
      <RowGrid border="bottom">
        <RowCell>
          <Box
            flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'baseline'}}
            style={{minWidth: 0}}
          >
            <Link to={assetDetailsPathForKey(asset.assetKey)}>
              <MiddleTruncate text={displayNameForAssetKey(asset.assetKey)} />
            </Link>
            <StatusBar
              targeted={targeted}
              inProgress={inProgress}
              succeeded={succeeded}
              failed={failed}
            />
          </Box>
        </RowCell>
        {asset.__typename === 'AssetPartitionsStatusCounts' ? (
          <>
            <RowCell>{numberFormatter.format(targeted)}</RowCell>
            <RowCell>{numberFormatter.format(inProgress)}</RowCell>
            <RowCell>{numberFormatter.format(succeeded)}</RowCell>
            <RowCell>{numberFormatter.format(failed)}</RowCell>
          </>
        ) : (
          <>
            <RowCell>-</RowCell>
            <RowCell>
              {inProgress ? (
                <div>
                  <Tag icon="spinner" intent="primary">
                    In progress
                  </Tag>
                </div>
              ) : (
                '-'
              )}
            </RowCell>
            <RowCell>
              {succeeded ? (
                <div>
                  <Tag intent="success">Succeeded</Tag>
                </div>
              ) : (
                '-'
              )}
            </RowCell>
            <RowCell>
              {failed ? (
                <div>
                  <Tag intent="danger">Failed</Tag>
                </div>
              ) : (
                '-'
              )}
            </RowCell>
          </>
        )}
      </RowGrid>
    </Row>
  );
};

const RowGrid = styled(Box)`
  display: grid;
  grid-template-columns: ${TEMPLATE_COLUMNS};
  height: 100%;
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

export function StatusBar({
  targeted,
  inProgress,
  succeeded,
  failed,
}: {
  targeted: number;
  inProgress: number;
  succeeded: number;
  failed: number;
}) {
  const pctSucceeded = (100 * succeeded) / targeted;
  const pctFailed = (100 * failed) / targeted;
  const pctInProgress = (100 * inProgress) / targeted;

  const pctFinal = Math.ceil(pctSucceeded + pctFailed);

  return (
    <Box flex={{direction: 'column', alignItems: 'flex-end', gap: 2}}>
      <div
        style={{
          borderRadius: '8px',
          backgroundColor: Colors.backgroundLight(),
          display: 'grid',
          gridTemplateColumns: `${pctSucceeded.toFixed(2)}% ${pctFailed.toFixed(2)}% ${pctInProgress.toFixed(2)}%`,
          gridTemplateRows: '100%',
          height: '12px',
          width: '200px',
          overflow: 'hidden',
        }}
      >
        <div style={{background: Colors.accentGreen()}} />
        <div style={{background: Colors.accentRed()}} />
        <div style={{background: Colors.accentBlue()}} />
      </div>
      <Caption color={Colors.textLight()}>{`${pctFinal}% completed`}</Caption>
    </Box>
  );
}
