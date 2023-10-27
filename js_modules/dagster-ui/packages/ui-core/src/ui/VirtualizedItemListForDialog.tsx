import {Box} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';

import {Container, Inner, Row} from './VirtualizedTable';

interface Props<T> {
  items: T[];
  renderItem: (item: T) => React.ReactNode;
  itemBorders?: boolean;
}

export function VirtualizedItemListForDialog<A>({items, renderItem, itemBorders = true}: Props<A>) {
  const container = React.useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => container.current,
    estimateSize: () => 40,
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const virtualItems = rowVirtualizer.getVirtualItems();

  return (
    <Container ref={container} style={{padding: '8px 24px'}}>
      <Inner $totalHeight={totalHeight}>
        {virtualItems.map(({index, key, size, start}) => {
          const assetKey = items[index]!;
          return (
            <Row $height={size} $start={start} key={key}>
              <Box
                style={{height: '100%'}}
                flex={{direction: 'row', alignItems: 'center'}}
                border={itemBorders && index < items.length - 1 ? 'bottom' : null}
              >
                {renderItem(assetKey)}
              </Box>
            </Row>
          );
        })}
      </Inner>
    </Container>
  );
}
