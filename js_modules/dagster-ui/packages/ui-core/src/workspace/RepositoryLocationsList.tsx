import {Box, NonIdealState, Spinner} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {useRef} from 'react';

import {
  CodeLocationRowType,
  VirtualizedCodeLocationHeader,
  VirtualizedCodeLocationRepositoryRow,
  VirtualizedCodeLocationRow,
} from './VirtualizedCodeLocationRow';
import {Container, DynamicRowContainer, Inner} from '../ui/VirtualizedTable';

interface Props {
  loading: boolean;
  codeLocations: CodeLocationRowType[];
  searchValue: string;
}

export const RepositoryLocationsList = ({loading, codeLocations, searchValue}: Props) => {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: codeLocations.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 64,
    overscan: 10,
  });

  const totalHeight = virtualizer.getTotalSize();
  const items = virtualizer.getVirtualItems();

  if (loading && !codeLocations.length) {
    return (
      <Box flex={{gap: 8, alignItems: 'center'}} padding={{horizontal: 24}}>
        <Spinner purpose="body-text" />
        <div>Loading…</div>
      </Box>
    );
  }

  if (!codeLocations.length) {
    if (searchValue) {
      return (
        <Box padding={{vertical: 32}}>
          <NonIdealState
            icon="folder"
            title="No matching code locations"
            description={
              <div>
                No code locations were found for search query <strong>{searchValue}</strong>.
              </div>
            }
          />
        </Box>
      );
    }

    return (
      <Box padding={{vertical: 32}}>
        <NonIdealState
          icon="folder"
          title="No code locations"
          description="When you add a code location, your definitions will appear here."
        />
      </Box>
    );
  }

  return (
    <Container ref={parentRef}>
      <VirtualizedCodeLocationHeader />
      <Inner $totalHeight={totalHeight}>
        <DynamicRowContainer $start={items[0]?.start ?? 0}>
          {items.map(({index, key}) => {
            const row: CodeLocationRowType = codeLocations[index]!;
            if (row.type === 'location') {
              return (
                <VirtualizedCodeLocationRow
                  key={key}
                  index={index}
                  locationEntry={row.locationEntry}
                  locationStatus={row.locationStatus}
                  ref={virtualizer.measureElement}
                />
              );
            }
            return (
              <VirtualizedCodeLocationRepositoryRow
                key={key}
                index={index}
                locationStatus={row.locationStatus}
                locationEntry={row.locationEntry}
                repository={row.repository}
                ref={virtualizer.measureElement}
              />
            );
          })}
        </DynamicRowContainer>
      </Inner>
    </Container>
  );
};
