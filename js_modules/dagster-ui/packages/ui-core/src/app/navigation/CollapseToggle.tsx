import {Button, Icon, Tooltip} from '@dagster-io/ui-components';
import {useContext} from 'react';

import {ShortcutHandler} from '../ShortcutHandler';
import {NavCollapseContext} from './NavCollapseProvider';

const isAltBShortcut = (event: KeyboardEvent) => {
  console.log('code', event.altKey, event.code, event.ctrlKey, event.metaKey, event.shiftKey);
  return (
    event.altKey && !event.shiftKey && !event.ctrlKey && !event.metaKey && event.code === 'KeyB'
  );
};

export const CollapseToggle = () => {
  const {isCollapsed, toggleCollapsed} = useContext(NavCollapseContext);

  const toggle = () => {
    debugger;
    toggleCollapsed();
  };

  return (
    <ShortcutHandler shortcutFilter={isAltBShortcut} shortcutLabel="⌥B" onShortcut={toggle}>
      <Tooltip
        content={isCollapsed ? 'Show navigation' : 'Hide navigation'}
        placement={isCollapsed ? 'right' : 'bottom'}
      >
        <Button
          icon={<Icon name={isCollapsed ? 'panel_show_left' : 'panel_show_right'} />}
          onClick={toggleCollapsed}
        />
      </Tooltip>
    </ShortcutHandler>
  );
};
