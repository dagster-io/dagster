import {Button, Icon, Tooltip} from '@dagster-io/ui-components';
import {useContext} from 'react';

import {NavCollapseContext} from './NavCollapseProvider';
import {ShortcutHandler} from '../ShortcutHandler';

const isAltBShortcut = (event: KeyboardEvent) => {
  return (
    event.altKey && !event.shiftKey && !event.ctrlKey && !event.metaKey && event.code === 'KeyB'
  );
};

export const CollapseToggle = () => {
  const {isCollapsed, toggleCollapsed, canCollapse} = useContext(NavCollapseContext);

  if (!canCollapse) {
    return null;
  }

  return (
    <ShortcutHandler
      shortcutFilter={isAltBShortcut}
      shortcutLabel="⌥B"
      onShortcut={toggleCollapsed}
    >
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
