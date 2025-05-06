import {BodySmall, Box, Colors, Icon, MiddleTruncate, Spinner} from '@dagster-io/ui-components';
import uniqueId from 'lodash/uniqueId';
import React, {useEffect, useMemo} from 'react';
import {Link} from 'react-router-dom';

import {statusToIconAndColor} from '../AssetHealthSummary';
import styles from './AssetSelectionSummaryTile.module.css';
import {useAssetsHealthData} from '../../asset-data/AssetHealthDataProvider';
import {useAssetSelectionFiltering} from '../../asset-selection/useAssetSelectionFiltering';
import {AssetHealthStatus} from '../../graphql/types';
import {numberFormatter} from '../../ui/formatters';
import {AssetTableFragment} from '../types/AssetTableFragment.types';
import {useAllAssets} from '../useAllAssets';
import {ViewType} from './util';

export const TILE_WIDTH = 230;
export const TILE_HEIGHT = 108;
export const TILE_GAP = 8;

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
    loading: assetsLoading,
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

    const loading = assetsLoading || assets.length > Object.keys(liveDataByNode).length;

    const statusCounts = useMemo(() => {
      return Object.values(liveDataByNode).reduce(
        (acc, data) => {
          let status: AssetHealthStatus = AssetHealthStatus.UNKNOWN;
          if (data.assetHealth?.assetHealth) {
            status = data.assetHealth.assetHealth;
          }
          if ([AssetHealthStatus.DEGRADED, AssetHealthStatus.WARNING].includes(status)) {
            // We only show degraded / warning statuses
            acc[status] = (acc[status] || 0) + 1;
          }
          return acc;
        },
        {} as Record<AssetHealthStatus, number>,
      );
    }, [liveDataByNode]);

    const degradedMeta = statusToIconAndColor[AssetHealthStatus.DEGRADED];
    const warningMeta = statusToIconAndColor[AssetHealthStatus.WARNING];

    const degradedJsx = statusCounts[AssetHealthStatus.DEGRADED] && (
      <Box className={styles.statusCountItem}>
        <Icon name={degradedMeta.iconName} color={degradedMeta.iconColor} />
        <BodySmall color={degradedMeta.textColor}>
          {numberFormatter.format(statusCounts[AssetHealthStatus.DEGRADED])}
        </BodySmall>
      </Box>
    );

    const warningJsx = statusCounts[AssetHealthStatus.WARNING] && (
      <Box className={styles.statusCountItem}>
        <Icon name={warningMeta.iconName} color={warningMeta.iconColor} />
        <BodySmall color={warningMeta.textColor}>
          {numberFormatter.format(statusCounts[AssetHealthStatus.WARNING])}
        </BodySmall>
      </Box>
    );

    return (
      <Link to={link} className={styles.tileLink}>
        <Box
          border="all"
          style={{
            width: TILE_WIDTH,
            height: TILE_HEIGHT,
          }}
          className={styles.tile}
        >
          <div className={styles.header}>
            <div>{icon}</div>
            <div className={styles.title} style={{color: Colors.textLight()}}>
              <MiddleTruncate text={label} />
            </div>
          </div>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
            <Box className={styles.assetCount} style={{color: Colors.textLight()}}>
              <Icon name="asset" color={Colors.textLight()} />
              {assetsLoading ? (
                <Spinner purpose="caption-text" />
              ) : (
                <BodySmall color={Colors.textLight()}>
                  {numberFormatter.format(assetCount)} assets
                </BodySmall>
              )}
            </Box>

            {assetsLoading ? null : loading ? (
              <Spinner purpose="caption-text" />
            ) : (
              <>
                {(degradedJsx || warningJsx) && <BodySmall color={Colors.textLight()}>•</BodySmall>}
                {degradedJsx}
                {warningJsx}
              </>
            )}
          </Box>
        </Box>
      </Link>
    );
  },
);
