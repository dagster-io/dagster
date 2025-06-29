import {Box, Container, Icon, Inner, MiddleTruncate} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {useMemo, useRef} from 'react';

import {AssetHealthFragment} from '../../asset-data/types/AssetHealthDataProvider.types';
import {AssetHealthStatusString, STATUS_INFO} from '../AssetHealthSummary';

interface Props {
  checkedDisplayKeys: Set<string>;
  groupedByStatus: Record<AssetHealthStatusString, AssetHealthFragment[]>;
}

export const SelectedAssetsPopoverContent = ({checkedDisplayKeys, groupedByStatus}: Props) => {
  const parentRef = useRef<HTMLDivElement>(null);

  const groupSets = useMemo(() => {
    return Object.fromEntries(
      Object.entries(groupedByStatus).map(([status, assets]) => {
        return [status, new Set(assets.map((asset) => JSON.stringify(asset.key.path)))];
      }),
    );
  }, [groupedByStatus]);

  const selectedAssets: {status: AssetHealthStatusString; key: string}[] = useMemo(() => {
    return Array.from(checkedDisplayKeys)
      .map((key) => {
        const matchingGroup = Object.entries(groupSets).find(([_, group]) => group.has(key));
        if (!matchingGroup) {
          return null;
        }
        const [status] = matchingGroup;
        return {status: status as AssetHealthStatusString, key};
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
              const item = selectedAssets[index]!;
              const {iconName, iconColor} = STATUS_INFO[item.status];
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
                  <Icon name={iconName} color={iconColor} />
                  <MiddleTruncate text={JSON.parse(item.key).join(' / ')} />
                </Box>
              );
            })}
          </div>
        </Inner>
      </Container>
    </div>
  );
};
