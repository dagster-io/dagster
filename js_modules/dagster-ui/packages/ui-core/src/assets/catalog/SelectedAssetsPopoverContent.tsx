import {Box, Container, Inner, MiddleTruncate} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {useMemo, useRef} from 'react';

import {Grouped} from './AssetCatalogV2VirtualizedTable';
import {tokenForAssetKey, tokenToAssetKey} from '../../asset-graph/Utils';
import {AssetHealthSummary} from '../AssetHealthSummary';
import styles from './SelectedAssetsPopoverContext.module.css';

type Props<T extends string> = {
  checkedDisplayKeys: Set<string>;
  grouped: Record<T, Grouped<T, any>>;
};

export const SelectedAssetsPopoverContent = <T extends string>({
  checkedDisplayKeys,
  grouped,
}: Props<T>) => {
  const parentRef = useRef<HTMLDivElement>(null);

  const groupSets = useMemo(() => {
    return Object.fromEntries(
      Object.entries(grouped).map(([group, _value]) => {
        const {assets} = _value as Grouped<T, any>;
        return [group as T, new Set(assets.map((asset) => tokenForAssetKey(asset.key)))];
      }),
    );
  }, [grouped]);

  const selectedAssets: {group: T; key: string}[] = useMemo(() => {
    return Array.from(checkedDisplayKeys)
      .map((key) => {
        const matchingGroup = Object.entries(groupSets).find(([_, group]) => group.has(key));
        if (!matchingGroup) {
          return null;
        }
        const [group] = matchingGroup;
        return {group: group as T, key};
      })
      .filter((asset) => asset !== null);
  }, [checkedDisplayKeys, groupSets]);

  const virtualizer = useVirtualizer({
    count: selectedAssets.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 32,
  });

  const totalHeight = virtualizer.getTotalSize();
  const items = virtualizer.getVirtualItems();

  return (
    <div style={{width: '400px', overflow: 'hidden'}}>
      <Container ref={parentRef} style={{maxHeight: '240px'}}>
        <Inner $totalHeight={totalHeight}>
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              transform: `translateY(${items[0]?.start ?? 0}px)`,
            }}
          >
            {items.map(({index, key}) => {
              const item = selectedAssets[index];
              if (!item) {
                return null;
              }
              return (
                <Box
                  key={key}
                  data-index={index}
                  ref={virtualizer.measureElement}
                  flex={{direction: 'row', alignItems: 'center', gap: 8}}
                  padding={{
                    top: index === 0 ? 12 : 8,
                    bottom: index === selectedAssets.length - 1 ? 12 : 8,
                    horizontal: 12,
                  }}
                >
                  <div className={styles.iconContainer}>
                    <AssetHealthSummary assetKey={tokenToAssetKey(item.key)} iconOnly />
                  </div>
                  <MiddleTruncate text={item.key} />
                </Box>
              );
            })}
          </div>
        </Inner>
      </Container>
    </div>
  );
};
