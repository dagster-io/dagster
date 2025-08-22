import {Icon} from '@dagster-io/ui-components';
import React from 'react';

import {AssetHealthFragment} from '../../asset-data/types/AssetHealthDataProvider.types';
import {AssetHealthStatusString, STATUS_INFO} from '../AssetHealthSummary';
import {AssetCatalogTableGroupHeaderRow} from './AssetCatalogTableGroupHeaderRow';

interface HeaderProps {
  status: AssetHealthStatusString;
  open: boolean;
  assets: AssetHealthFragment[];
  onToggleOpen: () => void;
  checkedState: 'checked' | 'indeterminate' | 'unchecked';
  onToggleChecked: (checked: boolean) => void;
}

export const HealthStatusHeaderRow = React.memo(
  ({status, open, assets, onToggleOpen, checkedState, onToggleChecked}: HeaderProps) => {
    const count = assets.length;
    const {iconName, iconColor, text} = STATUS_INFO[status];
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
