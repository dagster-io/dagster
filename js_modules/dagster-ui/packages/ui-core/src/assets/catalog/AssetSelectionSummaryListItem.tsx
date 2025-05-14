import {
  Box,
  Colors,
  IconWrapper,
  Menu,
  MiddleTruncate,
  Spinner,
  ifPlural,
} from '@dagster-io/ui-components';
import React, {useMemo} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import styles from './AssetSelectionSummaryTile.module.css';
import {ViewType, getThreadId, useAssetHealthStatuses} from './util';
import {useAssetSelectionFiltering} from '../../asset-selection/useAssetSelectionFiltering';
import {InsightsIcon, InsightsIconType} from '../../insights/InsightsIcon';
import {numberFormatter} from '../../ui/formatters';
import {AssetTableFragment} from '../types/AssetTableFragment.types';
import {useAllAssets} from '../useAllAssets';

export const AssetSelectionSummaryListItemFromSelection = React.memo(
  ({
    item,
  }: {
    icon: React.ReactNode;
    item: Extract<ViewType, {__typename: 'CatalogView'}>;
    menu: React.ReactNode;
  }) => {
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

export const AssetSelectionSummaryListItem = React.memo(
  ({
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
    loading?: boolean;
    threadId?: string;
  }) => {
    const {jsx, loading} = useAssetHealthStatuses({
      assets,
      threadId: useMemo(() => getThreadId(), []),
      loading: assetsLoading,
    });

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
                {jsx}
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
  },
);

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
