import {Icon} from '@dagster-io/ui-components';
import React, {useMemo} from 'react';

import {AssetHealthFragment} from '../../asset-data/types/AssetHealthDataProvider.types';
import {AssetHealthStatusString, STATUS_INFO} from '../AssetHealthSummary';
import {AssetCatalogTableGroupHeaderRow} from './AssetCatalogTableGroupHeaderRow';
import {AssetHealthGroupBy} from './AttributeStatusHeaderRow';

interface HeaderProps {
  status: AssetHealthStatusString;
  open: boolean;
  assets: AssetHealthFragment[];
  onToggleOpen: () => void;
  checkedState: 'checked' | 'indeterminate' | 'unchecked';
  onToggleChecked: (checked: boolean) => void;
  groupBy:
    | AssetHealthGroupBy.check_status
    | AssetHealthGroupBy.materialization_status
    | AssetHealthGroupBy.freshness_status
    | AssetHealthGroupBy.health_status;
}

export const HealthStatusHeaderRow = React.memo(
  ({status, open, assets, onToggleOpen, checkedState, onToggleChecked, groupBy}: HeaderProps) => {
    const count = assets.length;

    const {iconName, iconColor, text} = useMemo(() => {
      if (
        [AssetHealthGroupBy.check_status, AssetHealthGroupBy.freshness_status].includes(groupBy)
      ) {
        const iconName = STATUS_INFO[status].detailIcon;
        const iconColor = STATUS_INFO[status].iconColor;
        const text = STATUS_INFO[status].shortLabel;
        return {iconName, iconColor, text};
      } else if (groupBy === AssetHealthGroupBy.health_status) {
        const iconName = STATUS_INFO[status].trendIcon;
        const iconColor = STATUS_INFO[status].iconColor;
        const text = STATUS_INFO[status].displayName;
        return {iconName, iconColor, text};
      } else {
        const iconName = STATUS_INFO[status].detailIcon;
        const iconColor = STATUS_INFO[status].iconColor;
        const text = STATUS_INFO[status].materializationText;
        return {iconName, iconColor, text};
      }
    }, [status, groupBy]);

    return (
      <AssetCatalogTableGroupHeaderRow
        icon={<Icon name={iconName} color={iconColor} />}
        text={text}
        count={count}
        open={open}
        onToggleOpen={onToggleOpen}
        checkedState={checkedState}
        onToggleChecked={onToggleChecked}
      />
    );
  },
);

HealthStatusHeaderRow.displayName = 'HealthStatusHeaderRow';
