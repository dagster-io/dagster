import {ButtonGroup} from '@dagster-io/ui';
import * as React from 'react';

export const AssetViewModeSwitch: React.FC<{
  view: 'graph' | 'flat' | 'directory';
  setView: (view: 'graph' | 'flat' | 'directory') => void;
}> = ({view, setView}) => (
  <ButtonGroup
    activeItems={new Set([view])}
    buttons={[
      {id: 'graph', icon: 'gantt_waterfall', tooltip: 'Graph view'},
      {id: 'flat', icon: 'view_list', tooltip: 'List view'},
      {id: 'directory', icon: 'folder', tooltip: 'Folder view'},
    ]}
    onClick={setView}
  />
);
