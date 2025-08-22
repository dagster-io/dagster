import {Icon, IconName} from '@dagster-io/ui-components';
import React from 'react';

import {AssetCatalogTableGroupHeaderRow} from './AssetCatalogTableGroupHeaderRow';
import {AssetHealthFragment} from '../../asset-data/types/AssetHealthDataProvider.types';

export enum AssetHealthGroupBy {
  health_status = 'health_status',
  freshness_status = 'freshness_status',
  check_status = 'check_status',
  code_location = 'code_location',
  group = 'group',
  owner = 'owner',
  kind = 'kind',
  tags = 'tag',
}

export const ASSET_HEALTH_GROUP_BY_META: Record<
  AssetHealthGroupBy,
  {text: string; icon: IconName}
> = {
  [AssetHealthGroupBy.health_status]: {
    text: 'Health Status',
    icon: 'status',
  },
  [AssetHealthGroupBy.freshness_status]: {
    text: 'Freshness Status',
    icon: 'freshness',
  },
  [AssetHealthGroupBy.check_status]: {
    text: 'Check Status',
    icon: 'asset_check',
  },
  [AssetHealthGroupBy.code_location]: {
    text: 'Code Location',
    icon: 'repo',
  },
  [AssetHealthGroupBy.group]: {
    text: 'Group',
    icon: 'asset_group',
  },
  [AssetHealthGroupBy.owner]: {
    text: 'Owner',
    icon: 'account_circle',
  },
  [AssetHealthGroupBy.kind]: {
    text: 'Kind',
    icon: 'compute_kind',
  },
  [AssetHealthGroupBy.tags]: {
    text: 'Tag',
    icon: 'tag',
  },
};

export const GROUP_BY = [
  AssetHealthGroupBy.health_status,
  AssetHealthGroupBy.freshness_status,
  AssetHealthGroupBy.check_status,
  AssetHealthGroupBy.code_location,
  AssetHealthGroupBy.group,
  AssetHealthGroupBy.owner,
  AssetHealthGroupBy.kind,
  AssetHealthGroupBy.tags,
] as const;

export const GROUP_BY_ITEMS = GROUP_BY.map((key) => ({
  key,
  text: ASSET_HEALTH_GROUP_BY_META[key].text,
  icon: ASSET_HEALTH_GROUP_BY_META[key].icon,
}));

interface HeaderProps {
  text: string;
  groupBy: AssetHealthGroupBy;
  open: boolean;
  assets: AssetHealthFragment[];
  onToggleOpen: () => void;
  checkedState: 'checked' | 'indeterminate' | 'unchecked';
  onToggleChecked: (checked: boolean) => void;
}

export const AttributeStatusHeaderRow = React.memo(
  ({text, groupBy, open, assets, onToggleOpen, checkedState, onToggleChecked}: HeaderProps) => {
    let icon = null;
    if (ASSET_HEALTH_GROUP_BY_META[groupBy]) {
      icon = <Icon name={ASSET_HEALTH_GROUP_BY_META[groupBy].icon} />;
    }

    return (
      <AssetCatalogTableGroupHeaderRow
        icon={icon}
        text={text}
        count={assets.length}
        open={open}
        onToggleOpen={onToggleOpen}
        checkedState={checkedState}
        onToggleChecked={onToggleChecked}
      />
    );
  },
);

AttributeStatusHeaderRow.displayName = 'AttributeStatusHeaderRow';
