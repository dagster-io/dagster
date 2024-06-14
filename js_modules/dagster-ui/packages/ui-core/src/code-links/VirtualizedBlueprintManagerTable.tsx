import {useVirtualizer} from '@tanstack/react-virtual';
import {useRef} from 'react';

import {
  VirtualizedBlueprintManagerHeader,
  VirtualizedBlueprintManagerRow,
} from './VirtualizedBlueprintManagerRow';
import {BlueprintManagerFragment} from './types/WorkspaceBlueprintManagersRoot.types';
import {Container, Inner} from '../ui/VirtualizedTable';
import {RepoAddress} from '../workspace/types';

interface Props {
  repoAddress: RepoAddress;
  blueprintManagers: BlueprintManagerFragment[];
}

export const VirtualizedBlueprintManagerTable = ({repoAddress, blueprintManagers}: Props) => {
  const parentRef = useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: blueprintManagers.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 48,
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <div style={{overflow: 'hidden'}}>
      <Container ref={parentRef}>
        <VirtualizedBlueprintManagerHeader />
        <Inner $totalHeight={totalHeight}>
          {items.map(({index, key, size, start}) => {
            const row: BlueprintManagerFragment = blueprintManagers[index]!;
            return (
              <VirtualizedBlueprintManagerRow
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
  );
};
