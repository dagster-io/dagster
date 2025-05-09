import {
  BodySmall,
  Box,
  Colors,
  Icon,
  MiddleTruncate,
  Popover,
  Spinner,
  ifPlural,
} from '@dagster-io/ui-components';
import clsx from 'clsx';
import uniqueId from 'lodash/uniqueId';
import React, {useEffect, useMemo} from 'react';
import {Link} from 'react-router-dom';

import {statusToIconAndColor} from '../AssetHealthSummary';
import styles from './AssetSelectionSummaryTile.module.css';
import {useAssetsHealthData} from '../../asset-data/AssetHealthDataProvider';
import {useAssetSelectionFiltering} from '../../asset-selection/useAssetSelectionFiltering';
import {AssetHealthStatus} from '../../graphql/types';
import {compactNumberFormatter} from '../../ui/formatters';
import {AssetTableFragment} from '../types/AssetTableFragment.types';
import {useAllAssets} from '../useAllAssets';
import {ViewType} from './util';

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
        threadId={useMemo(() => uniqueId('health-thread-'), [])}
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
    threadId,
  }: {
    icon: React.ReactNode;
    label: string;
    assets: AssetTableFragment[];
    link: string;
    loading?: boolean;
    threadId?: string;
  }) => {
    const assetCount = assets.length;
    const {liveDataByNode} = useAssetsHealthData(
      useMemo(() => assets.map((asset) => asset.key), [assets]),
      threadId,
    );

    const assetsLoading = _assetsLoading && assets.length > 0;

    const loading = assetsLoading || assets.length > Object.keys(liveDataByNode).length;

    const statusCounts = useMemo(() => {
      return Object.values(liveDataByNode).reduce(
        (acc, data) => {
          let status: AssetHealthStatus = AssetHealthStatus.UNKNOWN;
          if (data.assetHealth?.assetHealth) {
            status = data.assetHealth.assetHealth;
          }
          acc[status] = (acc[status] || 0) + 1;
          return acc;
        },
        {} as Record<AssetHealthStatus, number>,
      );
    }, [liveDataByNode]);

    const degradedMeta = statusToIconAndColor[AssetHealthStatus.DEGRADED];
    const warningMeta = statusToIconAndColor[AssetHealthStatus.WARNING];
    const unknownMeta = statusToIconAndColor[AssetHealthStatus.UNKNOWN];
    const healthyMeta = statusToIconAndColor[AssetHealthStatus.HEALTHY];

    const degradedCount = statusCounts[AssetHealthStatus.DEGRADED];
    const degradedJsx = degradedCount && (
      <Popover
        content={
          <div>
            <BodySmall color={degradedMeta.textColor}>
              {compactNumberFormatter.format(degradedCount)}{' '}
              {ifPlural(degradedCount, 'asset', 'assets')} degraded
            </BodySmall>
          </div>
        }
      >
        <Box className={styles.statusCountItem}>
          <Icon name={degradedMeta.iconName} color={degradedMeta.iconColor} />
          <BodySmall color={Colors.textLight()}>
            {compactNumberFormatter.format(statusCounts[AssetHealthStatus.DEGRADED])}
          </BodySmall>
        </Box>
      </Popover>
    );

    const warningJsx = statusCounts[AssetHealthStatus.WARNING] && (
      <Box className={styles.statusCountItem}>
        <Icon name={warningMeta.iconName} color={warningMeta.iconColor} />
        <BodySmall color={Colors.textLight()}>
          {compactNumberFormatter.format(statusCounts[AssetHealthStatus.WARNING])}
        </BodySmall>
      </Box>
    );

    const unknownJsx = statusCounts[AssetHealthStatus.UNKNOWN] && (
      <Box className={styles.statusCountItem}>
        <Icon name={unknownMeta.iconName} color={unknownMeta.iconColor} />
        <BodySmall color={Colors.textLight()}>
          {compactNumberFormatter.format(statusCounts[AssetHealthStatus.UNKNOWN])}
        </BodySmall>
      </Box>
    );

    const healthyJsx = (
      <Box className={styles.statusCountItem}>
        <Icon name={healthyMeta.iconName} color={healthyMeta.iconColor} />
        <BodySmall color={Colors.textLight()}>
          {compactNumberFormatter.format(statusCounts[AssetHealthStatus.HEALTHY])}
        </BodySmall>
      </Box>
    );

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
          <div className={styles.footer}>
            {assetCount === 0 ? (
              <BodySmall color={Colors.textLight()}>No assets</BodySmall>
            ) : loading ? (
              <Spinner purpose="caption-text" />
            ) : (
              <Box flex={{direction: 'row', alignItems: 'center', gap: 6, wrap: 'wrap'}}>
                {healthyJsx}
                {degradedJsx}
                {warningJsx}
                {unknownJsx}
              </Box>
            )}
          </div>
        </Box>
      </Link>
    );
  },
);
