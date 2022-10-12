import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';

import {Container, Inner} from '../ui/VirtualizedTable';

import {VirtualizedScheduleHeader, VirtualizedScheduleRow} from './VirtualizedScheduleRow';
import {RepoAddress} from './types';

type Schedule = {name: string};

interface Props {
  repoAddress: RepoAddress;
  schedules: Schedule[];
}

export const VirtualizedScheduleTable: React.FC<Props> = ({repoAddress, schedules}) => {
  const parentRef = React.useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: schedules.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 64,
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <>
      <VirtualizedScheduleHeader />
      <div style={{overflow: 'hidden'}}>
        <Container ref={parentRef}>
          <Inner $totalHeight={totalHeight}>
            {items.map(({index, key, size, start}) => {
              const row: Schedule = schedules[index];
              return (
                <VirtualizedScheduleRow
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
