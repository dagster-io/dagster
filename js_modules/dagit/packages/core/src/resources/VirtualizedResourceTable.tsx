import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';

import {Container, Inner} from '../ui/VirtualizedTable';
import {RepoAddress} from '../workspace/types';

import {VirtualizedResourceHeader, VirtualizedResourceRow} from './VirtualizedResourceRow';
import {ResourceEntryFragment} from './types/WorkspaceResourcesRoot.types';

interface Props {
  repoAddress: RepoAddress;
  resources: ResourceEntryFragment[];
}

export const VirtualizedResourceTable: React.FC<Props> = ({repoAddress, resources}) => {
  const parentRef = React.useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: resources.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 64,
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <>
      <VirtualizedResourceHeader />
      <div style={{overflow: 'hidden'}}>
        <Container ref={parentRef}>
          <Inner $totalHeight={totalHeight}>
            {items.map(({index, key, size, start}) => {
              const row: ResourceEntryFragment = resources[index];
              return (
                <VirtualizedResourceRow
                  key={key}
                  repoAddress={repoAddress}
                  height={size}
                  start={start}
                  {...row}
                />
              );
            })}
          </Inner>
        </Container>
      </div>
    </>
  );
};
