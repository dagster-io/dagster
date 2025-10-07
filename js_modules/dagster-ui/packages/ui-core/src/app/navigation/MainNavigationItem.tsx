import clsx from 'clsx';
import {useHistory} from 'react-router-dom';

import {ShortcutHandler} from '../ShortcutHandler';
import styles from './css/MainNavigation.module.css';
import {NavigationItem} from './types';

interface MainNavigationItemProps {
  item: NavigationItem;
  collapsed: boolean;
}

export const MainNavigationItem = ({item, collapsed}: MainNavigationItemProps) => {
  const {element, right} = item;
  const history = useHistory();

  return (
    <div className={clsx(styles.itemContainer, collapsed && styles.collapsed)}>
      <ShortcutHandler
        shortcutFilter={item.shortcut?.filter}
        shortcutLabel={item.shortcut?.label}
        onShortcut={() => history.push(item.shortcut?.path ?? '')}
      >
        {element}
      </ShortcutHandler>
      {right && !collapsed ? <div className={styles.right}>{right}</div> : null}
    </div>
  );
};
