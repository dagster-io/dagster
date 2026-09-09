import {DagsterLogo, Icon, UnstyledButton} from '@dagster-io/ui-components';
import {MainNavigation} from '@shared/app/navigation/MainNavigation';
import clsx from 'clsx';
import {ReactNode, useContext} from 'react';
import {Link} from 'react-router-dom';

import {NavCollapseContext} from './NavCollapseProvider';
import styles from './css/AppContainer.module.css';
import {NavigationGroup} from './types';
import {useSearchDialog} from '../../search/SearchDialog';
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

  const showMobileChrome = isMobileScreen && !isFullScreenEnabled;

  return (
    <div className={styles.container}>
      {showMobileChrome ? (
        <MobileTopBar isOpen={isOpen} onToggleNav={isOpen ? close : open} />
      ) : null}
      {isMobileScreen && isOpen ? <div className={styles.backdrop} onClick={close} /> : null}
      <div
        className={clsx(
          styles.nav,
          isFullScreenEnabled ? styles.hidden : null,
          isCollapsed ? styles.collapsed : null,
          isMobileScreen && isOpen ? styles.mobileOpen : null,
        )}
        aria-hidden={isMobileScreen && !isOpen ? true : undefined}
      >
        {isMobileScreen ? (
          <div className={styles.drawerHeader}>
            <UnstyledButton className={styles.iconButton} onClick={close} aria-label="Close menu">
              <Icon name="close" size={24} />
            </UnstyledButton>
          </div>
        ) : null}
        <MainNavigation collapsed={isCollapsed} topGroups={topGroups} bottomGroups={bottomGroups} />
      </div>
      <div className={clsx(styles.main, isFullScreenEnabled ? styles.fullScreen : null)}>
        <div>{banner}</div>
        <div className={styles.child}>{children}</div>
      </div>
    </div>
  );
};

const MobileTopBar = ({isOpen, onToggleNav}: {isOpen: boolean; onToggleNav: () => void}) => {
  const {openSearch, overlay} = useSearchDialog();

  return (
    <div className={styles.mobileTopBar}>
      <UnstyledButton
        className={styles.iconButton}
        onClick={onToggleNav}
        aria-label="Toggle navigation"
        aria-expanded={isOpen}
      >
        <Icon name="menu" size={24} />
      </UnstyledButton>
      <Link to="/" className={styles.wordmark} aria-label="Home">
        <DagsterLogo height={24} />
      </Link>
      <UnstyledButton className={styles.iconButton} onClick={openSearch} aria-label="Search">
        <Icon name="search" size={24} />
      </UnstyledButton>
      {overlay}
    </div>
  );
};
