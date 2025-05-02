import {
  BodySmall,
  Box,
  Colors,
  Icon,
  IconWrapper,
  Menu,
  MiddleTruncate,
  Spinner,
  ifPlural,
} from '@dagster-io/ui-components';
import {useMemo} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import styles from './AssetSelectionSummaryTile.module.css';
import {ViewType} from './util';
import {useAssetsHealthData} from '../../asset-data/AssetHealthDataProvider';
import {useAssetSelectionFiltering} from '../../asset-selection/useAssetSelectionFiltering';
import {AssetHealthStatus} from '../../graphql/types';
import {InsightsIcon, InsightsIconType} from '../../insights/InsightsIcon';
import {numberFormatter} from '../../ui/formatters';
import {statusToIconAndColor} from '../AssetHealthSummary';
import {AssetTableFragment} from '../types/AssetTableFragment.types';
import {useAllAssets} from '../useAllAssets';

export const AssetSelectionSummaryListItemFromSelection = ({
  item,
}: {
  icon: React.ReactNode;
  item: Extract<ViewType, {__typename: 'CatalogView'}>;
  menu: React.ReactNode;
}) => {
  const {assets, loading} = useAllAssets();
  const {filtered} = useAssetSelectionFiltering({
    assets,
    assetSelection: item.selection.querySelection ?? '',
    loading,
    useWorker: false,
    includeExternalAssets: true,
  });
  return (
    <AssetSelectionSummaryListItem
      assets={filtered}
      icon={<InsightsIcon name={item.icon as InsightsIconType} size={16} />}
      label={item.name}
      link={item.link}
      menu={<Menu />}
      loading={loading}
    />
  );
};

export const AssetSelectionSummaryListItem = ({
  assets,
  icon,
  label,
  link,
  loading: assetsLoading,
}: {
  assets: AssetTableFragment[];
  icon: React.ReactNode;
  label: string;
  link: string;
  menu: React.ReactNode;
  loading: boolean;
}) => {
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
    <RowWrapper as={Link} to={link}>
      <Box
        padding={{horizontal: 24, vertical: 12}}
        flex={{alignItems: 'center', gap: 8, justifyContent: 'space-between'}}
        border="bottom"
      >
        <Box flex={{direction: 'row', alignItems: 'center', gap: 8}} className="row-icon">
          {icon}
          <MiddleTruncate text={label} />
        </Box>
        <Box flex={{direction: 'row', alignItems: 'center', gap: 12}}>
          {loading ? (
            <Spinner purpose="caption-text" />
          ) : (
            <Box className={styles.statusCountListWrapper} border="right" padding={{right: 12}}>
              {degradedJsx}
              {warningJsx}
            </Box>
          )}
          <span>
            {numberFormatter.format(assets.length)} asset
            {ifPlural(assets.length, '', 's')}
          </span>
        </Box>
      </Box>
    </RowWrapper>
  );
};

const RowWrapper = styled.div`
  &,
  &:hover {
    text-decoration: none;
    cursor: pointer;
  }
  color: ${Colors.textLight()};
  .row-icon {
    ${IconWrapper} {
      color: ${Colors.textLight()};
    }
    ${IconWrapper} {
      background: ${Colors.textLight()};
    }
  }
  cursor: pointer;
  &:hover {
    & {
      color: ${Colors.textDefault()};
    }
    .row-icon {
      ${IconWrapper} {
        color: ${Colors.textDefault()};
      }
      ${IconWrapper} {
        background: ${Colors.textDefault()};
      }
    }
  }
`;
