import {
  Box,
  Checkbox,
  Colors,
  Container,
  HorizontalControls,
  Icon,
  Inner,
  ListItem,
  Skeleton,
  SubtitleSmall,
  UnstyledButton,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React, {forwardRef, useMemo, useRef, useState} from 'react';
import {Link} from 'react-router-dom';

import {AssetHealthFragment} from '../../asset-data/types/AssetHealthDataProvider.types';
import {tokenForAssetKey} from '../../asset-graph/Utils';
import {numberFormatter} from '../../ui/formatters';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {AssetActionMenu} from '../AssetActionMenu';
import {AssetHealthStatusString, STATUS_INFO} from '../AssetHealthSummary';
import {AssetRecentUpdatesTrend} from '../AssetRecentUpdatesTrend';
import {assetDetailsPathForKey} from '../assetDetailsPathForKey';
import {useAllAssets} from '../useAllAssets';
import styles from './css/StatusHeaderContainer.module.css';

const shimmer = {shimmer: true};
const shimmerRows = [shimmer, shimmer, shimmer, shimmer, shimmer];

interface Props {
  groupedByStatus: Record<AssetHealthStatusString, AssetHealthFragment[]>;
  loading: boolean;
  healthDataLoading: boolean;
  checkedDisplayKeys: Set<string>;
  onToggleFactory: (id: string) => (values: {checked: boolean; shiftKey: boolean}) => void;
  onToggleGroup: (status: AssetHealthStatusString) => (checked: boolean) => void;
}

export const AssetCatalogV2VirtualizedTable = React.memo(
  ({
    groupedByStatus,
    loading,
    healthDataLoading,
    checkedDisplayKeys,
    onToggleFactory,
    onToggleGroup,
  }: Props) => {
    const containerRef = useRef<HTMLDivElement>(null);

    const [openStatuses, setOpenStatuses] = useState<Set<AssetHealthStatusString>>(
      new Set(['Unknown', 'Healthy', 'Warning', 'Degraded']),
    );

    const unGroupedRowItems = useMemo(() => {
      return Object.keys(groupedByStatus).flatMap((status_: string) => {
        const status = status_ as AssetHealthStatusString;
        if (!groupedByStatus[status].length) {
          return [];
        }
        if (openStatuses.has(status)) {
          return [{header: true, status}, ...groupedByStatus[status]];
        }
        return [{header: true, status}];
      });
    }, [groupedByStatus, openStatuses]);

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
            {items.map(({index, key}) => {
              // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
              const item = rowItems[index]!;

              const wrapper = (content: React.ReactNode) => (
                <div key={key} data-index={index} ref={rowVirtualizer.measureElement}>
                  {content}
                </div>
              );

              if ('shimmer' in item) {
                return wrapper(
                  <Box padding={{top: 12, horizontal: 20}}>
                    <Skeleton $height={30} $width="100%" />
                  </Box>,
                );
              }

              if ('header' in item) {
                const assetsInGroupJSON = groupedByStatus[item.status].map((asset) =>
                  JSON.stringify(asset.key.path),
                );

                const checkedState = assetsInGroupJSON.every((asset) =>
                  checkedDisplayKeys.has(asset),
                )
                  ? 'checked'
                  : assetsInGroupJSON.some((asset) => checkedDisplayKeys.has(asset))
                    ? 'indeterminate'
                    : 'unchecked';

                return (
                  <div key={key} data-index={index} ref={rowVirtualizer.measureElement}>
                    <StatusHeader
                      status={item.status}
                      open={openStatuses.has(item.status)}
                      assets={groupedByStatus[item.status]}
                      onToggleChecked={onToggleGroup(item.status)}
                      checkedState={checkedState}
                      onToggleOpen={() =>
                        setOpenStatuses((prev) => {
                          const newSet = new Set(prev);
                          if (newSet.has(item.status)) {
                            newSet.delete(item.status);
                          } else {
                            newSet.add(item.status);
                          }
                          return newSet;
                        })
                      }
                    />
                  </div>
                );
              }

              const path = JSON.stringify(item.key.path);
              return (
                <AssetRow
                  ref={rowVirtualizer.measureElement}
                  key={key}
                  asset={item}
                  index={index}
                  checked={checkedDisplayKeys.has(path)}
                  onToggle={onToggleFactory(path)}
                />
              );
            })}
          </div>
        </Inner>
      </Container>
    );
  },
);

interface HeaderProps {
  status: AssetHealthStatusString;
  open: boolean;
  assets: AssetHealthFragment[];
  onToggleOpen: () => void;
  checkedState: 'checked' | 'indeterminate' | 'unchecked';
  onToggleChecked: (checked: boolean) => void;
}

const StatusHeader = React.memo(
  ({status, open, assets, onToggleOpen, checkedState, onToggleChecked}: HeaderProps) => {
    const count = assets.length;
    const {iconName, iconColor, text} = STATUS_INFO[status];
    return (
      <Box
        flex={{direction: 'row', alignItems: 'center'}}
        className={styles.container}
        border="top-and-bottom"
      >
        <div className={styles.checkboxContainer}>
          <Checkbox
            type="checkbox"
            onChange={(e) => onToggleChecked(e.target.checked)}
            size="small"
            checked={checkedState !== 'unchecked'}
            indeterminate={checkedState === 'indeterminate'}
          />
        </div>
        <UnstyledButton onClick={onToggleOpen} style={{flex: 1}}>
          <Box
            flex={{direction: 'row', alignItems: 'center', gap: 4, justifyContent: 'space-between'}}
          >
            <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
              <Icon name={iconName} color={iconColor} />
              <SubtitleSmall>
                {text} ({numberFormatter.format(count)})
              </SubtitleSmall>
            </Box>
            <Box padding={{right: 8}}>
              <Icon
                name="arrow_drop_down"
                style={{transform: open ? 'rotate(0deg)' : 'rotate(-90deg)'}}
                color={Colors.textLight()}
              />
            </Box>
          </Box>
        </UnstyledButton>
      </Box>
    );
  },
);

StatusHeader.displayName = 'StatusHeader';

interface RowProps {
  asset: AssetHealthFragment;
  index: number;
  checked: boolean;
  onToggle: (values: {checked: boolean; shiftKey: boolean}) => void;
}

const AssetRow = forwardRef(
  ({asset, index, checked, onToggle}: RowProps, ref: React.ForwardedRef<HTMLDivElement>) => {
    const linkUrl = assetDetailsPathForKey({path: asset.key.path});

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
              {key: 'recent-updates', control: <AssetRecentUpdatesTrend asset={asset} />},
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
