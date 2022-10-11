import {Box, Colors} from '@dagster-io/ui';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';

import {Container, HeaderCell, Inner} from '../ui/VirtualizedTable';

import {VirtualizedSensorRow} from './VirtualizedSensorRow';
import {RepoAddress} from './types';
type Sensor = {name: string};

interface Props {
  repoAddress: RepoAddress;
  sensors: Sensor[];
}

export const VirtualizedSensorTable: React.FC<Props> = ({repoAddress, sensors}) => {
  const parentRef = React.useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: sensors.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 64,
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <>
      <Box
        border={{side: 'horizontal', width: 1, color: Colors.KeylineGray}}
        style={{
          display: 'grid',
          gridTemplateColumns: '76px 38% 30% 10% 20%',
          height: '32px',
          fontSize: '12px',
          color: Colors.Gray600,
        }}
      >
        <HeaderCell />
        <HeaderCell>Sensor name</HeaderCell>
        <HeaderCell>Frequency</HeaderCell>
        <HeaderCell>Last tick</HeaderCell>
        <HeaderCell>Last run</HeaderCell>
      </Box>
      <div style={{overflow: 'hidden'}}>
        <Container ref={parentRef}>
          <Inner $totalHeight={totalHeight}>
            {items.map(({index, key, size, start}) => {
              const row: Sensor = sensors[index];
              return (
                <VirtualizedSensorRow
                  key={key}
                  name={row.name}
                  repoAddress={repoAddress}
                  height={size}
                  start={start}
                />
              );
            })}
          </Inner>
        </Container>
      </div>
    </>
  );
};
