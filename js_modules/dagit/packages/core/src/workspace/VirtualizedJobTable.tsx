import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';

import {Container, Inner} from '../ui/VirtualizedTable';

import {VirtualizedJobHeader, VirtualizedJobRow} from './VirtualizedJobRow';
import {RepoAddress} from './types';

type Job = {isJob: boolean; name: string};

interface Props {
  repoAddress: RepoAddress;
  jobs: Job[];
}

export const VirtualizedJobTable: React.FC<Props> = ({repoAddress, jobs}) => {
  const parentRef = React.useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: jobs.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 64,
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <>
      <VirtualizedJobHeader />
      <div style={{overflow: 'hidden'}}>
        <Container ref={parentRef}>
          <Inner $totalHeight={totalHeight}>
            {items.map(({index, key, size, start}) => {
              const row: Job = jobs[index];
              return (
                <VirtualizedJobRow
                  key={key}
                  name={row.name}
                  isJob={row.isJob}
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
