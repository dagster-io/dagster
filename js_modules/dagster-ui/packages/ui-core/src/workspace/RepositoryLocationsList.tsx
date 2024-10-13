import {Box, NonIdealState, Row, Spinner} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {useRef} from 'react';

import {
  CodeLocationRowType,
  VirtualizedCodeLocationHeader,
  VirtualizedCodeLocationRepositoryRow,
  VirtualizedCodeLocationRow,
} from './VirtualizedCodeLocationRow';
import {Container, Inner} from '../ui/VirtualizedTable';

interface Props {
  loading: boolean;
  codeLocations: CodeLocationRowType[];
  searchValue: string;
  isFilteredView: boolean;
}

export const RepositoryLocationsList = ({
  loading,
  codeLocations,
  searchValue,
  isFilteredView,
}: Props) => {
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

    if (isFilteredView) {
      return (
        <Box padding={{vertical: 32}}>
          <NonIdealState
            icon="folder"
            title="No matching code locations"
            description={<div>No code locations were found for these filter settings.</div>}
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
        {items.map(({index, key, size, start}) => {
          const row: CodeLocationRowType = codeLocations[index]!;
          if (row.type === 'location') {
            return (
              <Row $height={size} $start={start} key={key}>
                <VirtualizedCodeLocationRow
                  index={index}
                  locationEntry={row.locationEntry}
                  locationStatus={row.locationStatus}
                  ref={virtualizer.measureElement}
                />
              </Row>
            );
          }
          return (
            <Row $height={size} $start={start} key={key}>
              <VirtualizedCodeLocationRepositoryRow
                index={index}
                locationStatus={row.locationStatus}
                locationEntry={row.locationEntry}
                repository={row.repository}
                ref={virtualizer.measureElement}
              />
            </Row>
          );
        })}
      </Inner>
    </Container>
  );
};
