// eslint-disable-next-line no-restricted-imports

import {CaptionMono} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {CSSProperties, useRef} from 'react';

import {displayNameForAssetKey} from '../asset-graph/Utils';
import {AssetKeyInput} from '../graphql/types';
import {Inner, Row} from '../ui/VirtualizedTable';

export const VirtualizedSimpleAssetKeyList = ({
  assetKeys,
  style,
}: {
  assetKeys: AssetKeyInput[];
  style?: CSSProperties;
}) => {
  const parentRef = useRef<HTMLDivElement>(null);
  const rowVirtualizer = useVirtualizer({
    count: assetKeys.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 18,
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <div style={{...style, overflowY: 'auto'}} ref={parentRef}>
      <Inner $totalHeight={totalHeight}>
        {items.map(({index, key, size, start}) => {
          const assetKey = assetKeys[index]!;
          return (
            <Row key={key} $height={size} $start={start}>
              <CaptionMono>{displayNameForAssetKey(assetKey)}</CaptionMono>
            </Row>
          );
        })}
      </Inner>
    </div>
  );
};
