import {gql} from '@apollo/client';
import {Body2, Box, Caption, Colors} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {linkToRunEvent} from '../../runs/RunUtils';
import {TimestampDisplay} from '../../schedules/TimestampDisplay';
import {testId} from '../../testing/testId';
import {HeaderCell, Row, RowCell, Container, Inner} from '../../ui/VirtualizedTable';
import {assetDetailsPathForAssetCheck} from '../assetDetailsPathForKey';

import {ASSET_CHECK_EXECUTION_FRAGMENT, MetadataCell} from './AssetCheckDetailModal';
import {AssetCheckStatusTag} from './AssetCheckStatusTag';
import {ExecuteChecksButton} from './ExecuteChecksButton';
import {ExecuteChecksButtonAssetNodeFragment} from './types/ExecuteChecksButton.types';
import {AssetCheckTableFragment} from './types/VirtualizedAssetCheckTable.types';

type Props = {
  assetNode: ExecuteChecksButtonAssetNodeFragment;
  rows: AssetCheckTableFragment[];
};

export const VirtualizedAssetCheckTable = ({assetNode, rows}: Props) => {
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
            const row: AssetCheckTableFragment = rows[index]!;
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

const TEMPLATE_COLUMNS = '2fr 150px 1fr 1.5fr 120px';

interface AssetCheckRowProps {
  row: AssetCheckTableFragment;
  assetNode: ExecuteChecksButtonAssetNodeFragment;
  height: number;
  start: number;
}

export const VirtualizedAssetCheckRow = ({assetNode, height, start, row}: AssetCheckRowProps) => {
  const execution = row.executionForLatestMaterialization;
  const timestamp = execution?.evaluation?.timestamp;

  return (
    <Row $height={height} $start={start} data-testid={testId(`row-#TODO_USE_CHECK_ID`)}>
      <RowGrid border="bottom">
        <RowCell style={{flexDirection: 'row', alignItems: 'center'}}>
          <Box flex={{direction: 'column', gap: 4}}>
            <Link
              to={assetDetailsPathForAssetCheck({assetKey: assetNode.assetKey, name: row.name})}
            >
              <Body2>{row.name}</Body2>
            </Link>
            <CaptionEllipsed>{row.description}</CaptionEllipsed>
          </Box>
        </RowCell>
        <RowCell style={{flexDirection: 'row', alignItems: 'center'}}>
          <div>
            <AssetCheckStatusTag execution={execution} />
          </div>
        </RowCell>
        <RowCell style={{flexDirection: 'row', alignItems: 'center'}}>
          {timestamp ? (
            <Link
              to={linkToRunEvent(
                {id: execution.runId},
                {stepKey: execution.stepKey, timestamp: execution.timestamp},
              )}
            >
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
            <ExecuteChecksButton
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
      border="top-and-bottom"
      style={{
        display: 'grid',
        gridTemplateColumns: TEMPLATE_COLUMNS,
        height: '32px',
        fontSize: '12px',
        color: Colors.textLight(),
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

export const ASSET_CHECK_TABLE_FRAGMENT = gql`
  fragment AssetCheckTableFragment on AssetCheck {
    name
    description
    canExecuteIndividually
    executionForLatestMaterialization {
      ...AssetCheckExecutionFragment
    }
  }
  ${ASSET_CHECK_EXECUTION_FRAGMENT}
`;
