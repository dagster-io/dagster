import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';

import {Container, Inner} from '../ui/VirtualizedTable';

import {VirtualizedSensorHeader, VirtualizedSensorRow} from './VirtualizedSensorRow';
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
      <VirtualizedSensorHeader />
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
