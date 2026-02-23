import {MainNavigation} from '@shared/app/navigation/MainNavigation';
import clsx from 'clsx';
import {ReactNode, useContext} from 'react';

import {NavCollapseContext} from './NavCollapseProvider';
import styles from './css/AppContainer.module.css';
import {NavigationGroup} from './types';

interface Props {
  topGroups: NavigationGroup[];
  bottomGroups: NavigationGroup[];
  banner?: ReactNode;
  isFullScreenEnabled?: boolean;
  children: ReactNode;
}

export const AppContainer = (props: Props) => {
  const {topGroups, bottomGroups, banner, children, isFullScreenEnabled = false} = props;

  const {isCollapsed} = useContext(NavCollapseContext);

  return (
    <div className={styles.container}>
      <div
        className={clsx(
          styles.nav,
          isFullScreenEnabled ? styles.hidden : null,
          isCollapsed ? styles.collapsed : null,
        )}
      >
        <MainNavigation collapsed={isCollapsed} topGroups={topGroups} bottomGroups={bottomGroups} />
      </div>
      <div className={clsx(styles.main, isFullScreenEnabled ? styles.fullScreen : null)}>
        <div>{banner}</div>
        <div className={styles.child}>{children}</div>
      </div>
    </div>
  );
};
