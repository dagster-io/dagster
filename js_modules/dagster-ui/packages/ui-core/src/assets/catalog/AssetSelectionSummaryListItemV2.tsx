import {
  BodySmall,
  Box,
  Colors,
  HorizontalControls,
  ListItem,
  MiddleTruncate,
} from '@dagster-io/ui-components';
import React, {useMemo} from 'react';
import {Link} from 'react-router-dom';

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
    useMemo(
      () => getHealthStatuses({liveDataByNode, loading, assetCount}),
      [liveDataByNode, loading, assetCount],
    );
    return (
      <AssetSelectionSummaryListItemWithHealthStatus
        index={index}
        icon={<InsightsIcon name={item.icon as InsightsIconType} size={16} />}
        label={item.name}
        link={item.link}
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
    const {loading} = useAssetHealthStatuses({
      assets,
      threadId: useMemo(() => getThreadId(), []),
      loading: assetsLoading,
    });

    return (
      <AssetSelectionSummaryListItemWithHealthStatus
        index={index}
        icon={icon}
        label={label}
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
    link,
    assetCount,
    index,
  }: {
    icon: React.ReactNode;
    label: string;
    link: string;
    loading?: boolean;
    assetCount: number;
    index: number;
  }) => {
    return (
      <ListItem
        href={link}
        index={index}
        renderLink={({href, ...rest}) => <Link to={href || '#'} {...rest} />}
        padding={{horizontal: 16, vertical: 12}}
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
                key: 'count',
                control: (
                  <Box padding={{left: 4}}>
                    <BodySmall color={Colors.textLight()}>
                      {assetCount === 1
                        ? '1 asset'
                        : `${numberFormatter.format(assetCount)} assets`}
                    </BodySmall>
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
