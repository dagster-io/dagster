import {
  Box,
  ButtonLink,
  Colors,
  MiddleTruncate,
  NonIdealState,
  Tag,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React, {useRef} from 'react';
import {Link, useHistory} from 'react-router-dom';
import styled from 'styled-components';

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
import {AssetKey, RunStatus} from '../../graphql/types';
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

function getRunsUrl(backfillId: string, status: 'inProgress' | 'complete' | 'failed' | 'targeted') {
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
        <Link to={getRunsUrl(backfill.id, 'complete')}>Succeeded</Link>
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
      <RowGrid border="bottom">
        <RowCell>
          <Box flex={{direction: 'row', justifyContent: 'space-between'}} style={{minWidth: 0}}>
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
              completed={completed}
              failed={failed}
            />
          </Box>
        </RowCell>
        {asset.__typename === 'AssetPartitionsStatusCounts' ? (
          <>
            <RowCell>{numberFormatter.format(targeted)}</RowCell>
            <RowCell>{numberFormatter.format(inProgress)}</RowCell>
            <RowCell>{numberFormatter.format(completed)}</RowCell>
            <RowCell>{numberFormatter.format(failed)}</RowCell>
          </>
        ) : (
          <>
            <RowCell>-</RowCell>
            <RowCell>
              {inProgress ? (
                <Tag icon="spinner" intent="primary">
                  In progress
                </Tag>
              ) : (
                '-'
              )}
            </RowCell>
            <RowCell>{completed ? <Tag intent="success">Completed</Tag> : '-'}</RowCell>
            <RowCell>{failed ? <Tag intent="danger">Failed</Tag> : '-'}</RowCell>
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
        backgroundColor: Colors.backgroundLight(),
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
      <div style={{background: Colors.accentGreen()}} />
      <div style={{background: Colors.accentRed()}} />
      <div style={{background: Colors.accentBlue()}} />
    </div>
  );
}
