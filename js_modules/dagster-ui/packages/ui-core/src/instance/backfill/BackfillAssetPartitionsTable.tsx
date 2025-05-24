import {
  Box,
  ButtonLink,
  Caption,
  Colors,
  MiddleTruncate,
  NonIdealState,
  Tag,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React, {useRef} from 'react';
import {Link, useHistory} from 'react-router-dom';
import clsx from 'clsx';

import styles from './BackfillAssetPartitionsTable.module.css';
import {
  BackfillPartitionsForAssetKeyQuery,
  BackfillPartitionsForAssetKeyQueryVariables,
} from './types/BackfillAssetPartitionsTable.types';
import {BackfillDetailsBackfillFragment} from './types/useBackfillDetailsQuery.types';
import {gql, useApolloClient} from '../../apollo-client';
import {displayNameForAssetKey, tokenForAssetKey} from '../../asset-graph/Utils';
import {asAssetKeyInput} from '../../assets/asInput';
import {assetDetailsPathForKey} from '../../assets/assetDetailsPathForKey';
import {AssetViewParams} from '../../assets/types';
import {AssetKey} from '../../graphql/types';
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

// Define CSS variable for template columns
document.documentElement.style.setProperty('--template-columns', TEMPLATE_COLUMNS);

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
            asset={assetStatuses[index]!}
            backfill={backfill}
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
  backfill,
  height,
  start,
}: {
  asset: AssetBackfillStatus;
  backfill: BackfillDetailsBackfillFragment;
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

  const client = useApolloClient();
  const history = useHistory();

  const onShowAssetDetails = async (assetKey: AssetKey, isPartitioned: boolean) => {
    let params: AssetViewParams = {};

    if (isPartitioned) {
      const resp = await client.query<
        BackfillPartitionsForAssetKeyQuery,
        BackfillPartitionsForAssetKeyQueryVariables
      >({
        query: BACKFILL_PARTITIONS_FOR_ASSET_KEY_QUERY,
        variables: {backfillId: backfill.id, assetKey: asAssetKeyInput(assetKey)},
      });
      const data =
        resp.data.partitionBackfillOrError.__typename === 'PartitionBackfill'
          ? resp.data.partitionBackfillOrError.partitionsTargetedForAssetKey
          : null;

      if (data && data.ranges?.length) {
        params = {default_range: data.ranges.map((r) => `[${r.start}...${r.end}]`).join(',')};
      }
    }
    return history.push(assetDetailsPathForKey(assetKey, params));
  };

  return (
    <Row
      $height={height}
      $start={start}
      data-testid={testId(`backfill-asset-row-${tokenForAssetKey(asset.assetKey)}`)}
    >
      <Box className={styles.rowGrid} border="bottom">
        <RowCell>
          <Box
            flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'baseline'}}
            style={{minWidth: 0}}
          >
            <ButtonLink
              style={{minWidth: 0}}
              onClick={() =>
                onShowAssetDetails(
                  asset.assetKey,
                  asset.__typename === 'AssetPartitionsStatusCounts',
                )
              }
            >
              <MiddleTruncate text={displayNameForAssetKey(asset.assetKey)} />
            </ButtonLink>
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
      </Box>
    </Row>
  );
};

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
        className={styles.statusBarContainer}
        style={{
          gridTemplateColumns: `${pctSucceeded.toFixed(2)}% ${pctFailed.toFixed(2)}% ${pctInProgress.toFixed(2)}%`,
          gridTemplateRows: '100%',
        }}
      >
        <div className={styles.statusBarSuccess} />
        <div className={styles.statusBarFailed} />
        <div className={styles.statusBarInProgress} />
      </div>
      <Caption color={Colors.textLight()}>{`${pctFinal}% completed`}</Caption>
    </Box>
  );
}
