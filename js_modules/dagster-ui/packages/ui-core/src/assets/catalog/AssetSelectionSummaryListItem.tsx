import {
  Box,
  HorizontalControls,
  ListItem,
  MiddleTruncate,
  Spinner,
} from '@dagster-io/ui-components';
import React, {useMemo} from 'react';
import {Link} from 'react-router-dom';

import styles from './AssetSelectionSummaryTile.module.css';
import {useSelectionHealthData} from './useSelectionHealthData';
import {ViewType, getHealthStatuses, getThreadId, useAssetHealthStatuses} from './util';
import {InsightsIcon, InsightsIconType} from '../../insights/InsightsIcon';
import {numberFormatter} from '../../ui/formatters';
import {AssetTableFragment} from '../types/AssetTableFragment.types';

export const AssetSelectionSummaryListItemFromSelection = React.memo(
  ({index, item}: {index: number; item: Extract<ViewType, {__typename: 'CatalogView'}>}) => {
    const {liveDataByNode, assetCount, loading} = useSelectionHealthData({
      selection: item.selection.querySelection ?? '',
    });
    const {jsx} = useMemo(
      () => getHealthStatuses({liveDataByNode, loading, assetCount}),
      [liveDataByNode, loading, assetCount],
    );
    return (
      <AssetSelectionSummaryListItemWithHealthStatus
        index={index}
        icon={<InsightsIcon name={item.icon as InsightsIconType} size={16} />}
        label={item.name}
        link={item.link}
        statusJsx={jsx}
        loading={loading}
        assetCount={assetCount}
      />
    );
  },
);

interface AssetSelectionSummaryListItemProps {
  index: number;
  assets: AssetTableFragment[];
  icon: React.ReactNode;
  label: string;
  link: string;
  loading?: boolean;
}

export const AssetSelectionSummaryListItem = React.memo(
  ({
    index,
    assets,
    icon,
    label,
    link,
    loading: assetsLoading,
  }: AssetSelectionSummaryListItemProps) => {
    const {jsx, loading} = useAssetHealthStatuses({
      assets,
      threadId: useMemo(() => getThreadId(), []),
      loading: assetsLoading,
    });

    return (
      <AssetSelectionSummaryListItemWithHealthStatus
        index={index}
        icon={icon}
        label={label}
        statusJsx={jsx}
        link={link}
        assetCount={assets.length}
        loading={loading}
      />
    );
  },
);

export const AssetSelectionSummaryListItemWithHealthStatus = React.memo(
  ({
    icon,
    label,
    statusJsx,
    link,
    loading,
    assetCount,
    index,
  }: {
    icon: React.ReactNode;
    label: string;
    link: string;
    statusJsx: React.ReactNode;
    loading?: boolean;
    assetCount: number;
    index: number;
  }) => {
    return (
      <ListItem
        href={link}
        index={index}
        renderLink={({href, ...rest}) => <Link to={href || '#'} {...rest} />}
        left={
          <Box flex={{direction: 'row', alignItems: 'center', gap: 8}} className="row-icon">
            {icon}
            <MiddleTruncate text={label} />
          </Box>
        }
        right={
          <HorizontalControls
            controls={[
              {
                key: 'status',
                control: loading ? (
                  <Spinner purpose="caption-text" />
                ) : (
                  <div className={styles.statusCountListWrapper}>{statusJsx}</div>
                ),
              },
              {
                key: 'count',
                control: (
                  <Box padding={{left: 4}}>
                    {assetCount === 1 ? '1 asset' : `${numberFormatter.format(assetCount)} assets`}
                  </Box>
                ),
              },
            ]}
          />
        }
      />
    );
  },
);
