import {Icon, UnstyledButton} from '@dagster-io/ui-components';
import {MainNavigation} from '@shared/app/navigation/MainNavigation';
import clsx from 'clsx';
import {ReactNode, useContext} from 'react';
import {Link} from 'react-router-dom';

import {DaggyWordmark} from './DaggyWordmark';
import {NavCollapseContext} from './NavCollapseProvider';
import styles from './css/AppContainer.module.css';
import {NavigationGroup} from './types';
import {LayoutContext} from '../LayoutProvider';

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
  const {nav} = useContext(LayoutContext);
  const {isMobileScreen, isOpen, open, close} = nav;

  return (
    <div className={styles.container}>
      {isMobileScreen && !isFullScreenEnabled ? (
        <div className={styles.mobileTopBar}>
          <UnstyledButton
            className={styles.menuButton}
            onClick={isOpen ? close : open}
            aria-label="Toggle navigation"
          >
            <Icon name="menu" size={24} />
          </UnstyledButton>
          <Link to="/">
            <DaggyWordmark />
          </Link>
        </div>
      ) : null}
      {isMobileScreen && isOpen ? <div className={styles.backdrop} onClick={close} /> : null}
      <div
        className={clsx(
          styles.nav,
          isFullScreenEnabled ? styles.hidden : null,
          isCollapsed ? styles.collapsed : null,
          isMobileScreen && isOpen ? styles.mobileOpen : null,
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
