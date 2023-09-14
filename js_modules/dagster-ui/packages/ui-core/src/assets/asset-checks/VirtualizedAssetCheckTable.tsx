import {Body2, Box, Caption, Colors} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {TimestampDisplay} from '../../schedules/TimestampDisplay';
import {testId} from '../../testing/testId';
import {HeaderCell, Row, RowCell, Container, Inner} from '../../ui/VirtualizedTable';
import {assetDetailsPathForKey} from '../assetDetailsPathForKey';

import {MetadataCell} from './AssetCheckDetailModal';
import {AssetCheckStatusTag} from './AssetCheckStatusTag';
import {EvaluateChecksAssetNode, ExexcuteChecksButton} from './ExecuteChecksButton';
import {AssetChecksQuery} from './types/AssetChecks.types';

type Check = Extract<
  AssetChecksQuery['assetChecksOrError'],
  {__typename: 'AssetChecks'}
>['checks'][0];

type Props = {
  assetNode: EvaluateChecksAssetNode;
  rows: Check[];
};

export const VirtualizedAssetCheckTable: React.FC<Props> = ({assetNode, rows}: Props) => {
  const parentRef = React.useRef<HTMLDivElement | null>(null);
  const count = rows.length;

  const rowVirtualizer = useVirtualizer({
    count,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 64,
    overscan: 5,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <div style={{overflow: 'hidden'}}>
      <Container ref={parentRef}>
        <VirtualizedAssetCheckHeader />
        <Inner $totalHeight={totalHeight}>
          {items.map(({index, key, size, start}) => {
            const row: Check = rows[index]!;
            return (
              <VirtualizedAssetCheckRow
                assetNode={assetNode}
                key={key}
                height={size}
                start={start}
                row={row}
              />
            );
          })}
        </Inner>
      </Container>
    </div>
  );
};

const TEMPLATE_COLUMNS = '2fr 150px 1fr 1fr 140px';

interface AssetCheckRowProps {
  assetNode: EvaluateChecksAssetNode;
  height: number;
  start: number;
  row: Check;
}

export const VirtualizedAssetCheckRow = ({assetNode, height, start, row}: AssetCheckRowProps) => {
  const execution = row.executionForLatestMaterialization;
  const timestamp = execution?.evaluation?.timestamp;

  return (
    <Row $height={height} $start={start} data-testid={testId(`row-#TODO_USE_CHECK_ID`)}>
      <RowGrid border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}>
        <RowCell style={{flexDirection: 'row', alignItems: 'center'}}>
          <Box flex={{direction: 'column', gap: 4}}>
            <Link
              to={assetDetailsPathForKey(assetNode.assetKey, {
                view: 'checks',
                checkDetail: row.name,
              })}
            >
              <Body2>{row.name}</Body2>
            </Link>
            <CaptionEllipsed>{row.description}</CaptionEllipsed>
          </Box>
        </RowCell>
        <RowCell style={{flexDirection: 'row', alignItems: 'center'}}>
          <div>
            <AssetCheckStatusTag check={row} execution={row.executionForLatestMaterialization} />
          </div>
        </RowCell>
        <RowCell style={{flexDirection: 'row', alignItems: 'center'}}>
          {timestamp ? (
            <Link to={`/runs/${execution.runId}`}>
              <TimestampDisplay timestamp={timestamp} />
            </Link>
          ) : (
            ' - '
          )}
        </RowCell>
        <RowCell>
          <MetadataCell metadataEntries={execution?.evaluation?.metadataEntries} />
        </RowCell>
        <RowCell>
          <Box flex={{justifyContent: 'flex-end'}}>
            <ExexcuteChecksButton
              assetNode={assetNode}
              checks={[row]}
              label="Execute"
              icon={false}
            />
          </Box>
        </RowCell>
      </RowGrid>
    </Row>
  );
};

const CaptionEllipsed = styled(Caption)`
  text-overflow: ellipsis;
  max-width: 100%;
  overflow: hidden;
  white-space: nowrap;
`;

export const VirtualizedAssetCheckHeader = () => {
  return (
    <Box
      border={{side: 'horizontal', width: 1, color: Colors.KeylineGray}}
      style={{
        display: 'grid',
        gridTemplateColumns: TEMPLATE_COLUMNS,
        height: '32px',
        fontSize: '12px',
        color: Colors.Gray600,
      }}
    >
      <HeaderCell>Check name</HeaderCell>
      <HeaderCell>Status</HeaderCell>
      <HeaderCell>Evaluation timestamp</HeaderCell>
      <HeaderCell>Evaluation metadata</HeaderCell>
      <HeaderCell>Actions</HeaderCell>
    </Box>
  );
};

const RowGrid = styled(Box)`
  display: grid;
  grid-template-columns: ${TEMPLATE_COLUMNS};
  height: 100%;
`;
