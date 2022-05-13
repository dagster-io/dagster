import {ButtonGroup, ButtonGroupItem} from '@dagster-io/ui';
import * as React from 'react';
import {useHistory} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';

import {AssetViewType, useAssetView} from './useAssetView';

export const AssetViewModeSwitch = () => {
  const history = useHistory();
  const [view, _setView] = useAssetView();
  const {flagExperimentalAssetDAG} = useFeatureFlags();

  const buttons: ButtonGroupItem<AssetViewType>[] = [
    {id: 'graph', icon: 'gantt_waterfall', tooltip: 'Graph view'},
    {id: 'flat', icon: 'view_list', tooltip: 'List view'},
    {id: 'directory', icon: 'folder', tooltip: 'Folder view'},
  ];
  if (flagExperimentalAssetDAG) {
    buttons.unshift({id: 'grid', icon: 'source', tooltip: 'Grid view'});
  }

  const setView = (view: AssetViewType) => {
    _setView(view);
    if (view === 'graph') {
      history.push('/instance/asset-graph');
    } else if (view === 'grid') {
      history.push('/instance/asset-grid');
    } else if (history.location.pathname !== '/instance/assets') {
      history.push('/instance/assets');
    }
  };

  return <ButtonGroup activeItems={new Set([view])} buttons={buttons} onClick={setView} />;
};
