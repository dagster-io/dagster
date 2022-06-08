import {ButtonGroup, ButtonGroupItem} from '@dagster-io/ui';
import * as React from 'react';
import {useHistory} from 'react-router-dom';

import {AssetViewType, useAssetView} from './useAssetView';

export const AssetViewModeSwitch = () => {
  const history = useHistory();
  const [view, setView] = useAssetView();

  const buttons: ButtonGroupItem<AssetViewType>[] = [
    {id: 'flat', icon: 'view_list', tooltip: 'List view'},
    {id: 'directory', icon: 'folder', tooltip: 'Folder view'},
  ];

  const onClick = (view: AssetViewType) => {
    setView(view);
    if (history.location.pathname !== '/instance/assets') {
      history.push('/instance/assets');
    }
  };

  return <ButtonGroup activeItems={new Set([view])} buttons={buttons} onClick={onClick} />;
};
