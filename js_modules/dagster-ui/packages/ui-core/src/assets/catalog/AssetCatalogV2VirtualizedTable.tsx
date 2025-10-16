import {
  Box,
  Container,
  HorizontalControls,
  HoverButton,
  Icon,
  Inner,
  ListItem,
  Skeleton,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React, {forwardRef, useMemo, useRef} from 'react';
import {Link} from 'react-router-dom';

import {usePrefixedCacheKey} from '../../app/usePrefixedCacheKey';
import {tokenForAssetKey} from '../../asset-graph/Utils';
import {useStateWithStorage} from '../../hooks/useStateWithStorage';
import {TimeFromNow} from '../../ui/TimeFromNow';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {AssetActionMenu} from '../AssetActionMenu';
import {AssetHealthSummary} from '../AssetHealthSummary';
import {AssetRecentUpdatesTrend, EventPopover} from '../AssetRecentUpdatesTrend';
import {assetDetailsPathForKey} from '../assetDetailsPathForKey';
import {useAllAssets} from '../useAllAssets';
import {useAssetRecentUpdates} from '../useAssetRecentUpdates';

const shimmer = {shimmer: true};
const shimmerRows = [shimmer, shimmer, shimmer, shimmer, shimmer];

export type Grouped<T extends string, TAsset extends {key: {path: string[]}}> = {
  assets: TAsset[];
  renderGroupHeader: (props: {
    group: T;
    open: boolean;
    assets: TAsset[];
    onToggleChecked: (checked: boolean) => void;
    checkedState: 'checked' | 'indeterminate' | 'unchecked';
    onToggleOpen: () => void;
  }) => React.ReactNode;
  isNone?: boolean;
};

export type AssetCatalogV2VirtualizedTableProps<
  T extends string,
  TAsset extends {key: {path: string[]}},
> = {
  id: string;
  allGroups: T[];
  grouped: Record<T, Grouped<T, TAsset>>;
  loading: boolean;
  healthDataLoading: boolean;
  checkedDisplayKeys: Set<string>;
  onToggleFactory: (id: string) => (values: {checked: boolean; shiftKey: boolean}) => void;
  onToggleGroup: (group: T) => (checked: boolean) => void;
};

const AssetCatalogV2VirtualizedTableImpl = <
  T extends string,
  TAsset extends {key: {path: string[]}},
>({
  id,
  allGroups,
  grouped,
  loading,
  healthDataLoading,
  checkedDisplayKeys,
  onToggleFactory,
  onToggleGroup,
}: AssetCatalogV2VirtualizedTableProps<T, TAsset>) => {
  const containerRef = useRef<HTMLDivElement>(null);

  const [closedGroupsArray, setClosedGroups] = useStateWithStorage<T[]>(
    usePrefixedCacheKey(id),
    (json) => {
      if (json instanceof Array) {
        return json;
      }
      return [];
    },
  );

  const closedGroups = useMemo(() => new Set(closedGroupsArray), [closedGroupsArray]);

  const unGroupedRowItems = useMemo(() => {
    return allGroups.flatMap((group) => {
      if (!grouped[group]?.assets.length) {
        return [];
      }
      if (!closedGroups.has(group)) {
        return [
          {header: true, group},
          ...grouped[group].assets.map((asset) => ({
            ...asset,
            group,
          })),
        ];
      }
      return [{header: true, group}];
    });
  }, [allGroups, grouped, closedGroups]);

  const rowItems = useMemo(() => {
    if (loading) {
      return shimmerRows;
    }
    if (healthDataLoading) {
      return [...unGroupedRowItems, ...shimmerRows];
    }
    return unGroupedRowItems;
  }, [healthDataLoading, loading, unGroupedRowItems]);

  const rowVirtualizer = useVirtualizer({
    count: rowItems.length,
    getScrollElement: () => containerRef.current,
    estimateSize: () => 44,
    overscan: 5,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <Container ref={containerRef}>
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
          {items.map(({index}) => {
            const item = rowItems[index];

            if (!item) {
              return null;
            }

            if ('shimmer' in item) {
              return (
                <div key={index} data-index={index} ref={rowVirtualizer.measureElement}>
                  <Box padding={{top: 12, horizontal: 20}}>
                    <Skeleton $height={30} $width="100%" />
                  </Box>
                </div>
              );
            }

            if ('header' in item) {
              const assetsInGroup =
                grouped[item.group]?.assets.map((asset) => tokenForAssetKey(asset.key)) ?? [];

              const checkedState = assetsInGroup.every((asset) => checkedDisplayKeys.has(asset))
                ? 'checked'
                : assetsInGroup.some((asset) => checkedDisplayKeys.has(asset))
                  ? 'indeterminate'
                  : 'unchecked';

              const Klass = grouped[item.group]?.renderGroupHeader;

              return (
                <div key={item.group} data-index={index} ref={rowVirtualizer.measureElement}>
                  {Klass ? (
                    <Klass
                      group={item.group}
                      open={!closedGroups.has(item.group)}
                      assets={grouped[item.group].assets}
                      onToggleChecked={onToggleGroup(item.group)}
                      checkedState={checkedState}
                      onToggleOpen={() =>
                        setClosedGroups((prev) => {
                          if (prev.includes(item.group)) {
                            return prev.filter((group) => group !== item.group);
                          }
                          return [...prev, item.group];
                        })
                      }
                    />
                  ) : (
                    <div>{item.group}</div>
                  )}
                </div>
              );
            }

            return (
              <AssetRow
                ref={rowVirtualizer.measureElement}
                key={`${item.group}-${tokenForAssetKey(item.key)}`}
                asset={item}
                index={index}
                checked={checkedDisplayKeys.has(tokenForAssetKey(item.key))}
                onToggle={onToggleFactory(tokenForAssetKey(item.key))}
              />
            );
          })}
        </div>
      </Inner>
    </Container>
  );
};

export const AssetCatalogV2VirtualizedTable = React.memo(
  AssetCatalogV2VirtualizedTableImpl,
) as typeof AssetCatalogV2VirtualizedTableImpl;

interface RowProps<TAsset> {
  asset: TAsset;
  index: number;
  checked: boolean;
  onToggle: (values: {checked: boolean; shiftKey: boolean}) => void;
}

const AssetRow = forwardRef(
  <TAsset extends {key: {path: string[]}}>(
    {asset, index, checked, onToggle}: RowProps<TAsset>,
    ref: React.ForwardedRef<HTMLDivElement>,
  ) => {
    const linkUrl = assetDetailsPathForKey({path: asset.key.path});
    const {recentEvents, latestInfo, loading} = useAssetRecentUpdates({asset});
    const lastEvent = recentEvents[0];
    const latestInfoItem =
      latestInfo?.inProgressRunIds.length || latestInfo?.unstartedRunIds.length
        ? latestInfo
        : undefined;

    const {assets} = useAllAssets();
    const definition = useMemo(
      () =>
        assets?.find(
          (workspaceAsset) => tokenForAssetKey(workspaceAsset.key) === tokenForAssetKey(asset.key),
        )?.definition,
      [assets, asset.key],
    );

    const repoAddress = definition?.repository
      ? buildRepoAddress(definition.repository.name, definition.repository.location.name)
      : null;

    return (
      <ListItem
        ref={ref}
        href={linkUrl}
        checked={checked}
        onToggle={onToggle}
        renderLink={({href, ...props}) => <Link to={href || '#'} {...props} />}
        index={index}
        left={
          <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
            <Icon name="asset" />
            {asset.key.path.join(' / ')}
          </Box>
        }
        right={
          <HorizontalControls
            controls={[
              {
                key: 'recent-updates',
                control:
                  loading && !lastEvent ? (
                    <Skeleton $width={100} $height={21} />
                  ) : (
                    <>
                      <EventPopover event={lastEvent}>
                        {lastEvent ? (
                          <HoverButton>
                            <TimeFromNow
                              unixTimestamp={Number(lastEvent.timestamp) / 1000}
                              showTooltip={false}
                            />
                          </HoverButton>
                        ) : (
                          ' - '
                        )}
                      </EventPopover>
                    </>
                  ),
              },
              {
                key: 'recent-events',
                control: (
                  <Box padding={{horizontal: 8}}>
                    <AssetRecentUpdatesTrend events={recentEvents} latestInfo={latestInfoItem} />
                  </Box>
                ),
              },
              {
                key: 'asset-health',
                control: <AssetHealthSummary assetKey={asset.key} iconOnly />,
              },
              {
                key: 'action-menu',
                control: (
                  <AssetActionMenu
                    unstyledButton
                    path={asset.key.path}
                    definition={definition || null}
                    repoAddress={repoAddress}
                  />
                ),
              },
            ]}
          />
        }
      />
    );
  },
);

AssetRow.displayName = 'AssetRow';
