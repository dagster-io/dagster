import {
  Box,
  Colors,
  IconWrapper,
  MiddleTruncate,
  Spinner,
  ifPlural,
} from '@dagster-io/ui-components';
import React, {useMemo} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import styles from './AssetSelectionSummaryTile.module.css';
import {useSelectionHealthData} from './useSelectionHealthData';
import {ViewType, getHealthStatuses, getThreadId, useAssetHealthStatuses} from './util';
import {InsightsIcon, InsightsIconType} from '../../insights/InsightsIcon';
import {numberFormatter} from '../../ui/formatters';
import {AssetTableFragment} from '../types/AssetTableFragment.types';

export const AssetSelectionSummaryListItemFromSelection = React.memo(
  ({
    item,
  }: {
    icon: React.ReactNode;
    item: Extract<ViewType, {__typename: 'CatalogView'}>;
    menu: React.ReactNode;
  }) => {
    const assetSelection = item.selection.querySelection ?? '';

    const {liveDataByNode, loading, assetCount} = useSelectionHealthData({
      selection: assetSelection,
    });
    const {jsx} = useMemo(
      () => getHealthStatuses({liveDataByNode, loading, assetCount}),
      [liveDataByNode, loading, assetCount],
    );
    return (
      <AssetSelectionSummaryListItemWithHealthStatus
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

export const AssetSelectionSummaryListItem = React.memo(
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
    const {jsx, loading} = useAssetHealthStatuses({
      assets,
      threadId: useMemo(() => getThreadId(), []),
      loading: _assetsLoading,
    });

    return (
      <AssetSelectionSummaryListItemWithHealthStatus
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
  }: {
    icon: React.ReactNode;
    label: string;
    link: string;
    statusJsx: React.ReactNode;
    loading?: boolean;
    assetCount: number;
  }) => {
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
                {statusJsx}
              </Box>
            )}
            <span>
              {numberFormatter.format(assetCount)} asset
              {ifPlural(assetCount, '', 's')}
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
