import {ButtonGroup, ButtonGroupItem} from '@dagster-io/ui';
import * as React from 'react';

import {AssetViewType, useAssetView} from './useAssetView';

export const AssetViewModeSwitch = () => {
  const [view, setView] = useAssetView();

  const buttons: ButtonGroupItem<AssetViewType>[] = [
    {id: 'flat', icon: 'view_list', tooltip: 'List view'},
    {id: 'directory', icon: 'folder', tooltip: 'Folder view'},
  ];

  return <ButtonGroup activeItems={new Set([view])} buttons={buttons} onClick={setView} />;
};
