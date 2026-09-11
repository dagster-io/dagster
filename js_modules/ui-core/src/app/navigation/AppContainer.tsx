import {DagsterLogo, Icon, UnstyledButton} from '@dagster-io/ui-components';
import {MainNavigation} from '@shared/app/navigation/MainNavigation';
import clsx from 'clsx';
import {ReactNode, RefObject, useContext, useEffect, useLayoutEffect, useRef} from 'react';
import {Link} from 'react-router-dom';

import {NavCollapseContext} from './NavCollapseProvider';
import styles from './css/AppContainer.module.css';
import {NavigationGroup} from './types';
import {usePrevious} from '../../hooks/usePrevious';
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
  const isDrawerHidden = isMobileScreen && !isOpen;

  const drawerRef = useRef<HTMLDivElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  // The closed drawer is only translated offscreen; `inert` removes its links
  // from the tab order and from assistive tech. Set as a DOM property because
  // the React 18 types don't declare the attribute.
  useLayoutEffect(() => {
    if (drawerRef.current) {
      drawerRef.current.inert = isDrawerHidden;
    }
  }, [isDrawerHidden]);

  // Move focus into the drawer when it opens and back to the hamburger when it
  // closes, so keyboard users never end up on an invisible control.
  const wasOpen = usePrevious(isOpen);
  useEffect(() => {
    if (!isMobileScreen || wasOpen === undefined || wasOpen === isOpen) {
      return;
    }
    if (isOpen) {
      closeButtonRef.current?.focus();
      return;
    }
    const active = document.activeElement;
    if (!active || active === document.body || drawerRef.current?.contains(active)) {
      toggleRef.current?.focus();
    }
  }, [isMobileScreen, isOpen, wasOpen]);

  useEffect(() => {
    if (!isMobileScreen || !isOpen) {
      return;
    }
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        close();
      }
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [isMobileScreen, isOpen, close]);

  return (
    <div className={styles.container}>
      {showMobileChrome ? (
        <MobileTopBar isOpen={isOpen} onToggleNav={isOpen ? close : open} toggleRef={toggleRef} />
      ) : null}
      {isMobileScreen && isOpen ? <div className={styles.backdrop} onClick={close} /> : null}
      <div
        ref={drawerRef}
        className={clsx(
          styles.nav,
          isFullScreenEnabled ? styles.hidden : null,
          isCollapsed ? styles.collapsed : null,
          isMobileScreen && isOpen ? styles.mobileOpen : null,
        )}
        aria-hidden={isDrawerHidden ? true : undefined}
      >
        {isMobileScreen ? (
          <div className={styles.drawerHeader}>
            <UnstyledButton
              ref={closeButtonRef}
              className={styles.iconButton}
              onClick={close}
              aria-label="Close menu"
            >
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

const MobileTopBar = ({
  isOpen,
  onToggleNav,
  toggleRef,
}: {
  isOpen: boolean;
  onToggleNav: () => void;
  toggleRef: RefObject<HTMLButtonElement>;
}) => {
  const {openSearch, overlay} = useSearchDialog();

  return (
    <div className={styles.mobileTopBar}>
      <UnstyledButton
        ref={toggleRef}
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
