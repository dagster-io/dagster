import {
  Box,
  HorizontalControls,
  ListItem,
  Menu,
  MiddleTruncate,
  Spinner,
} from '@dagster-io/ui-components';
import React, {useMemo} from 'react';
import {Link} from 'react-router-dom';

import styles from './AssetSelectionSummaryTile.module.css';
import {ViewType, getThreadId, useAssetHealthStatuses} from './util';
import {useAssetSelectionFiltering} from '../../asset-selection/useAssetSelectionFiltering';
import {InsightsIcon, InsightsIconType} from '../../insights/InsightsIcon';
import {numberFormatter} from '../../ui/formatters';
import {AssetTableFragment} from '../types/AssetTableFragment.types';
import {useAllAssets} from '../useAllAssets';

export const AssetSelectionSummaryListItemFromSelection = React.memo(
  ({index, item}: {index: number; item: Extract<ViewType, {__typename: 'CatalogView'}>}) => {
    const {assets, loading} = useAllAssets();
    const {filtered, loading: filteredLoading} = useAssetSelectionFiltering({
      assets,
      assetSelection: item.selection.querySelection ?? '',
      loading,
      useWorker: false,
      includeExternalAssets: true,
    });
    return (
      <AssetSelectionSummaryListItem
        index={index}
        assets={filtered}
        icon={<InsightsIcon name={item.icon as InsightsIconType} size={16} />}
        label={item.name}
        link={item.link}
        menu={<Menu />}
        loading={loading || filteredLoading}
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
  menu: React.ReactNode;
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
                  <Box
                    className={styles.statusCountListWrapper}
                    border="right"
                    padding={{right: 12}}
                  >
                    {jsx}
                  </Box>
                ),
              },
              {
                key: 'count',
                control: (
                  <span>
                    {assets.length === 1
                      ? '1 asset'
                      : `${numberFormatter.format(assets.length)} assets`}
                  </span>
                ),
              },
            ]}
          />
        }
      />
    );
  },
);
