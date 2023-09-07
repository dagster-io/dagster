import {Body2, Box, Caption, Colors} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {AssetKeyInput} from '../../graphql/types';
import {TimestampDisplay} from '../../schedules/TimestampDisplay';
import {testId} from '../../testing/testId';
import {HeaderCell, Row, RowCell, Container, Inner} from '../../ui/VirtualizedTable';
import {assetDetailsPathForKey} from '../assetDetailsPathForKey';

import {MetadataCell} from './AssetCheckDetailModal';
import {AssetCheckStatusTag} from './AssetCheckStatusTag';
import {AssetChecksQuery} from './types/AssetChecks.types';

type Check = Extract<
  AssetChecksQuery['assetChecksOrError'],
  {__typename: 'AssetChecks'}
>['checks'][0];

type Props = {
  assetKey: AssetKeyInput;
  rows: Check[];
};

export const VirtualizedAssetCheckTable: React.FC<Props> = ({assetKey, rows}: Props) => {
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
                assetKey={assetKey}
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

const TEMPLATE_COLUMNS = '2fr 120px 1fr 1fr';

interface AssetCheckRowProps {
  assetKey: AssetKeyInput;
  height: number;
  start: number;
  row: Check;
}

export const VirtualizedAssetCheckRow = ({assetKey, height, start, row}: AssetCheckRowProps) => {
  const execution = row.executionForLatestMaterialization;
  const timestamp = execution?.evaluation?.timestamp;

  const status = React.useMemo(() => {
    if (!execution) {
      return <AssetCheckStatusTag notChecked={true} />;
    }
    return (
      <AssetCheckStatusTag status={execution.status} severity={execution.evaluation?.severity} />
    );
  }, [execution]);

  return (
    <Row $height={height} $start={start} data-testid={testId(`row-#TODO_USE_CHECK_ID`)}>
      <RowGrid border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}>
        <RowCell style={{flexDirection: 'row', alignItems: 'center'}}>
          <Box flex={{direction: 'column', gap: 4}}>
            <Link
              to={assetDetailsPathForKey(assetKey, {
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
          <div>{status}</div>
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
    </Box>
  );
};

const RowGrid = styled(Box)`
  display: grid;
  grid-template-columns: ${TEMPLATE_COLUMNS};
  height: 100%;
`;
