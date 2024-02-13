import {useVirtualizer} from '@tanstack/react-virtual';
import {useRef} from 'react';

import {VirtualizedJobHeader, VirtualizedJobRow} from './VirtualizedJobRow';
import {RepoAddress} from './types';
import {Container, Inner} from '../ui/VirtualizedTable';

type Job = {isJob: boolean; name: string};

interface Props {
  repoAddress: RepoAddress;
  jobs: Job[];
}

export const VirtualizedJobTable = ({repoAddress, jobs}: Props) => {
  const parentRef = useRef<HTMLDivElement | null>(null);

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
              const row: Job = jobs[index]!;
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
