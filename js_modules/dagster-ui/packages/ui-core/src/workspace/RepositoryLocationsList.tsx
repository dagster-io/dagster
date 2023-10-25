import {Box, NonIdealState, Spinner} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';

import {Container, DynamicRowContainer, Inner} from '../ui/VirtualizedTable';

import {
  CodeLocationRowType,
  VirtualizedCodeLocationErrorRow,
  VirtualizedCodeLocationHeader,
  VirtualizedCodeLocationRow,
} from './VirtualizedCodeLocationRow';

interface Props {
  loading: boolean;
  codeLocations: CodeLocationRowType[];
  searchValue: string;
}

export const RepositoryLocationsList = ({loading, codeLocations, searchValue}: Props) => {
  const parentRef = React.useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: codeLocations.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 64,
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  if (loading && !items.length) {
    return (
      <Box flex={{gap: 8, alignItems: 'center'}} padding={{horizontal: 24}}>
        <Spinner purpose="body-text" />
        <div>Loading...</div>
      </Box>
    );
  }

  if (!items.length) {
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
    <>
      <VirtualizedCodeLocationHeader />
      <div style={{overflow: 'hidden'}}>
        <Container ref={parentRef}>
          <Inner $totalHeight={totalHeight}>
            <DynamicRowContainer $start={items[0]?.start ?? 0}>
              {items.map(({index, key}) => {
                const row: CodeLocationRowType = codeLocations[index]!;
                if (row.type === 'error') {
                  return (
                    <VirtualizedCodeLocationErrorRow
                      key={key}
                      data-index={index}
                      locationNode={row.node}
                      measure={rowVirtualizer.measure}
                    />
                  );
                }

                return (
                  <VirtualizedCodeLocationRow
                    key={key}
                    data-index={index}
                    codeLocation={row.codeLocation}
                    repository={row.repository}
                    measure={rowVirtualizer.measure}
                  />
                );
              })}
            </DynamicRowContainer>
          </Inner>
        </Container>
      </div>
    </>
  );
};
