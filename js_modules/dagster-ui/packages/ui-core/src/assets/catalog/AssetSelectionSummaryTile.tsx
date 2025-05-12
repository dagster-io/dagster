import {Box, Colors, MiddleTruncate} from '@dagster-io/ui-components';
import clsx from 'clsx';
import React, {useEffect, useMemo} from 'react';
import {Link} from 'react-router-dom';

import styles from './AssetSelectionSummaryTile.module.css';
import {useAssetSelectionFiltering} from '../../asset-selection/useAssetSelectionFiltering';
import {AssetTableFragment} from '../types/AssetTableFragment.types';
import {useAllAssets} from '../useAllAssets';
import {ViewType, getThreadId, useAssetHealthStatues} from './util';

export const TILE_WIDTH = 272;
export const TILE_HEIGHT = 104;
export const TILE_GAP = 12;

// An in memory cache to side step slow asset selection filtering when revisiting the page.
// To fix this properly we need to add more caches within useAssetSelectionFiltering and useAssetGraphData but it is difficult to do so
// since the array of nodes they receive aren't the same when you visit the page again since they're the result of `.filter` calls.
const memoryCache = new Map<string, {assets: any[]}>();

export const AssetSelectionSummaryTileFromSelection = React.memo(
  ({
    icon,
    selection,
  }: {
    icon: React.ReactNode;
    selection: Extract<ViewType, {__typename: 'CatalogView'}>;
  }) => {
    const assetSelection = selection.selection.querySelection ?? '';
    const {assets: allAssets, loading: allAssetsLoading} = useAllAssets();

    const {filtered, loading: filteredLoading} = useAssetSelectionFiltering({
      assets: allAssets,
      assetSelection,
      loading: allAssetsLoading,
      useWorker: false,
      includeExternalAssets: true,
    });

    useEffect(() => {
      if (filtered.length > 0) {
        memoryCache.set(assetSelection, {assets: filtered});
      }
    }, [filtered, assetSelection]);

    const assets = filtered.length ? filtered : (memoryCache.get(assetSelection)?.assets ?? []);

    const loading = filteredLoading && assets.length === 0;

    return (
      <AssetSelectionSummaryTile
        icon={icon}
        label={selection.name}
        assets={assets}
        link={selection.link}
        loading={loading}
      />
    );
  },
);

export const AssetSelectionSummaryTile = React.memo(
  ({
    icon,
    label,
    assets,
    link,
    loading: _assetsLoading,
  }: {
    icon: React.ReactNode;
    label: string;
    assets: AssetTableFragment[];
    link: string;
    loading?: boolean;
    threadId?: string;
  }) => {
    const {jsx, loading} = useAssetHealthStatues({
      assets,
      threadId: useMemo(() => getThreadId(), []),
      loading: _assetsLoading,
    });

    return (
      <Link to={link} className={styles.tileLink}>
        <Box
          border="all"
          style={{
            minWidth: TILE_WIDTH,
            minHeight: TILE_HEIGHT,
          }}
          className={clsx(styles.tile, loading && styles.tileLoading)}
        >
          <div className={styles.header}>
            <div>{icon}</div>
            <div className={styles.title} style={{color: Colors.textLight()}}>
              <MiddleTruncate text={label} />
            </div>
          </div>
          <div className={styles.footer}>{jsx}</div>
        </Box>
      </Link>
    );
  },
);
