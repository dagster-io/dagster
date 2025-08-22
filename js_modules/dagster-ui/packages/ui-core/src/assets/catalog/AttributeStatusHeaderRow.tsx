import {Icon, IconName} from '@dagster-io/ui-components';
import React from 'react';

import {AssetCatalogTableGroupHeaderRow} from './AssetCatalogTableGroupHeaderRow';

export enum AssetHealthGroupBy {
  health_status = 'health_status',
  freshness_status = 'freshness_status',
  check_status = 'check_status',
  materialization_status = 'materialization_status',
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
  [AssetHealthGroupBy.materialization_status]: {
    text: 'Materialization Status',
    icon: 'materialization',
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
  AssetHealthGroupBy.materialization_status,
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

interface HeaderProps<TAsset extends {key: {path: string[]}}> {
  text: string;
  groupBy: AssetHealthGroupBy;
  open: boolean;
  assets: TAsset[];
  onToggleOpen: () => void;
  checkedState: 'checked' | 'indeterminate' | 'unchecked';
  onToggleChecked: (checked: boolean) => void;
  noneGroup: string;
}

export const NONE_KEY = '__<None>__asfoiahgoih1309419205i9i5jigj1__#$#@%@%3425'; // random constant string for uniqueness

export const AttributeStatusHeaderRow = React.memo(
  <TAsset extends {key: {path: string[]}}>({
    text,
    groupBy,
    open,
    assets,
    onToggleOpen,
    checkedState,
    onToggleChecked,
    noneGroup,
  }: HeaderProps<TAsset>) => {
    let icon = null;
    if (ASSET_HEALTH_GROUP_BY_META[groupBy]) {
      icon = <Icon name={ASSET_HEALTH_GROUP_BY_META[groupBy].icon} />;
    }

    return (
      <AssetCatalogTableGroupHeaderRow
        icon={icon}
        text={text === NONE_KEY ? noneGroup : text}
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
