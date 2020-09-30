import {Colors} from '@blueprintjs/core';
import {uniq} from 'lodash';
import * as React from 'react';
import styled from 'styled-components/macro';

import {AssetQuery_assetOrError_Asset_historicalMaterializations} from 'src/assets/types/AssetQuery';
import {useViewport} from 'src/gaant/useViewport';
import {GridColumn, GridScrollContainer, TopLabelTilted} from 'src/partitions/RunMatrixUtils';

const BOX_COL_WIDTH = 23;

const OVERSCROLL = 150;

interface PartitionRunMatrixProps {
  values: AssetQuery_assetOrError_Asset_historicalMaterializations[];
}

export const AssetPartitionMatrix: React.FunctionComponent<PartitionRunMatrixProps> = (props) => {
  const {viewport, containerProps} = useViewport();
  const [focusedPartition, setFocusedPartition] = React.useState<string>('');

  const sorted = [...props.values]
    .filter((a) => a.partition)
    .sort((a, b) => a.partition!.localeCompare(b.partition!));

  const partitionColumns = uniq(sorted.map((v) => v.partition)).map((name) => ({
    name: name as string,
    present: sorted.some((p) => p.partition === name),
  }));

  const visibleRangeStart = Math.max(0, Math.floor((viewport.left - OVERSCROLL) / BOX_COL_WIDTH));
  const visibleCount = Math.ceil((viewport.width + OVERSCROLL * 2) / BOX_COL_WIDTH);
  const visibleColumns = partitionColumns.slice(
    visibleRangeStart,
    visibleRangeStart + visibleCount,
  );

  return (
    <PartitionRunMatrixContainer>
      <div style={{position: 'relative', display: 'flex', border: `1px solid ${Colors.GRAY5}`}}>
        <GridScrollContainer {...containerProps}>
          <div
            style={{
              width: partitionColumns.length * BOX_COL_WIDTH,
              position: 'relative',
              height: 80,
            }}
          >
            {visibleColumns.map((p, idx) => (
              <GridColumn
                key={p.name}
                focused={p.name === focusedPartition}
                onClick={() => setFocusedPartition(p.name)}
                style={{
                  width: BOX_COL_WIDTH,
                  position: 'absolute',
                  zIndex: visibleColumns.length - idx,
                  left: (idx + visibleRangeStart) * BOX_COL_WIDTH,
                }}
              >
                <TopLabelTilted>
                  <div className="tilted">{p.name}</div>
                </TopLabelTilted>
                <div key={p.name} className={`square ${p.present ? 'success' : 'missing'}`} />
              </GridColumn>
            ))}
          </div>
        </GridScrollContainer>
      </div>
      {visibleColumns.length === 0 && <EmptyMessage>No data to display.</EmptyMessage>}
    </PartitionRunMatrixContainer>
  );
};

const EmptyMessage = styled.div`
  padding: 20px;
  text-align: center;
`;

const PartitionRunMatrixContainer = styled.div`
  display: block;
  margin-bottom: 20px;
`;
