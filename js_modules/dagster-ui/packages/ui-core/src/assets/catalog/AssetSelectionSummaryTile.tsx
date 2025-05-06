import {BodySmall, Box, Colors, Icon, MiddleTruncate, Spinner} from '@dagster-io/ui-components';
import React, {useMemo} from 'react';
import {Link} from 'react-router-dom';

import {statusToIconAndColor} from '../AssetHealthSummary';
import styles from './AssetSelectionSummaryTile.module.css';
import {useAssetsHealthData} from '../../asset-data/AssetHealthDataProvider';
import {useAssetSelectionFiltering} from '../../asset-selection/useAssetSelectionFiltering';
import {AssetHealthStatus} from '../../graphql/types';
import {numberFormatter} from '../../ui/formatters';
import {AssetTableFragment} from '../types/AssetTableFragment.types';
import {useAllAssets} from '../useAllAssets';

export const TILE_WIDTH = 230;
export const TILE_HEIGHT = 108;
export const TILE_GAP = 8;

export const AssetSelectionSummaryTileFromSelection = React.memo(
  ({
    icon,
    label,
    selection,
    link,
  }: {
    icon: React.ReactNode;
    label: string;
    selection: string;
    link: string;
  }) => {
    const {assets, loading} = useAllAssets();
    const {filtered} = useAssetSelectionFiltering({
      assets,
      assetSelection: selection,
      loading,
      useWorker: false,
      includeExternalAssets: true,
    });

    return (
      <AssetSelectionSummaryTile
        icon={icon}
        label={label}
        assets={filtered}
        link={link}
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
    loading: assetsLoading,
  }: {
    icon: React.ReactNode;
    label: string;
    assets: AssetTableFragment[];
    link: string;
    loading?: boolean;
  }) => {
    const assetCount = assets.length;
    const {liveDataByNode} = useAssetsHealthData(
      useMemo(() => assets.map((asset) => asset.key), [assets]),
    );

    const loading = assetsLoading || assets.length !== Object.keys(liveDataByNode).length;

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

    const degradedJsx = statusCounts[AssetHealthStatus.DEGRADED] && (
      <Box className={styles.statusCountItem}>
        <Icon
          name={statusToIconAndColor[AssetHealthStatus.DEGRADED].iconName}
          color={statusToIconAndColor[AssetHealthStatus.DEGRADED].iconColor}
        />
        <BodySmall color={statusToIconAndColor[AssetHealthStatus.DEGRADED].textColor}>
          {numberFormatter.format(statusCounts[AssetHealthStatus.DEGRADED])}
        </BodySmall>
      </Box>
    );

    const warningJsx = statusCounts[AssetHealthStatus.WARNING] && (
      <Box className={styles.statusCountItem}>
        <Icon
          name={statusToIconAndColor[AssetHealthStatus.WARNING].iconName}
          color={statusToIconAndColor[AssetHealthStatus.WARNING].iconColor}
        />
        <BodySmall color={statusToIconAndColor[AssetHealthStatus.WARNING].textColor}>
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
              <BodySmall color={Colors.textLight()}>{assetCount.toLocaleString()} assets</BodySmall>
            </Box>
            {loading ? (
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
