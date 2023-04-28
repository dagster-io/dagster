import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';

import {BasicInstigationStateFragment} from '../overview/types/BasicInstigationStateFragment.types';
import {makeSensorKey} from '../sensors/makeSensorKey';
import {Container, Inner} from '../ui/VirtualizedTable';

import {VirtualizedSensorHeader, VirtualizedSensorRow} from './VirtualizedSensorRow';
import {RepoAddress} from './types';

type SensorInfo = {name: string; sensorState: BasicInstigationStateFragment};

interface Props {
  repoAddress: RepoAddress;
  sensors: SensorInfo[];
  headerCheckbox: React.ReactNode;
  checkedKeys: Set<string>;
  onToggleCheckFactory: (path: string) => (values: {checked: boolean; shiftKey: boolean}) => void;
}

export const VirtualizedSensorTable = ({
  repoAddress,
  sensors,
  headerCheckbox,
  checkedKeys,
  onToggleCheckFactory,
}: Props) => {
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
      <VirtualizedSensorHeader checkbox={headerCheckbox} />
      <div style={{overflow: 'hidden'}}>
        <Container ref={parentRef}>
          <Inner $totalHeight={totalHeight}>
            {items.map(({index, key, size, start}) => {
              const row: SensorInfo = sensors[index];
              const sensorKey = makeSensorKey(repoAddress, row.name);
              return (
                <VirtualizedSensorRow
                  key={key}
                  name={row.name}
                  repoAddress={repoAddress}
                  sensorState={row.sensorState}
                  checked={checkedKeys.has(sensorKey)}
                  showCheckboxColumn={!!headerCheckbox}
                  onToggleChecked={onToggleCheckFactory(sensorKey)}
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
