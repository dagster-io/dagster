import {Box, Colors} from '@dagster-io/ui';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';

import {Container, Inner, Row} from '../../ui/VirtualizedTable';

interface Props<A> {
  assetKeys: A[];
  renderItem: (assetKey: A) => React.ReactNode;
}

export function VirtualizedAssetListForDialog<A>({assetKeys, renderItem}: Props<A>) {
  const container = React.useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: assetKeys.length,
    getScrollElement: () => container.current,
    estimateSize: () => 40,
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <Container ref={container} style={{padding: '8px 24px'}}>
      <Inner $totalHeight={totalHeight}>
        {items.map(({index, key, size, start}) => {
          const assetKey = assetKeys[index]!;
          return (
            <Row $height={size} $start={start} key={key}>
              <Box
                style={{height: '100%'}}
                flex={{direction: 'row', alignItems: 'center'}}
                border={
                  index < assetKeys.length - 1
                    ? {side: 'bottom', width: 1, color: Colors.KeylineGray}
                    : null
                }
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
