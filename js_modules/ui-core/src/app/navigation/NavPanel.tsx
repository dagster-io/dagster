import {Button, Icon} from '@dagster-io/ui-components';
import {MainNavigation} from '@shared/app/navigation/MainNavigation';
import clsx from 'clsx';
import {RefObject, useContext, useEffect, useRef} from 'react';

import {NavCollapseContext} from './NavCollapseProvider';
import styles from './css/AppContainer.module.css';
import {NavigationGroup} from './types';
import {LayoutContext} from '../LayoutProvider';

interface Props {
  // Render as an off-canvas drawer (mobile layout) rather than the desktop sidebar.
  asDrawer: boolean;
  isFullScreenEnabled: boolean;
  topGroups: NavigationGroup[];
  bottomGroups: NavigationGroup[];
}

// The drawer never collapses; it has its own close button.
const DRAWER_COLLAPSE_CONTEXT = {isCollapsed: false, toggleCollapsed: () => {}, canCollapse: false};

/**
 * The main navigation, as a sidebar on desktop or a drawer on mobile.
 *
 * Both modes are rendered by this one component with the same element structure rather
 * than as two components, because the mode can change after the page has mounted (a route
 * reports its mobile status from a layout effect) and swapping component types would
 * remount the nav. The drawer-only pieces are the backdrop and close button.
 */
export const NavPanel = ({asDrawer, isFullScreenEnabled, topGroups, bottomGroups}: Props) => {
  const {nav} = useContext(LayoutContext);
  const collapseContext = useContext(NavCollapseContext);

  const isCollapsed = !asDrawer && collapseContext.isCollapsed;
  const isDrawerOpen = asDrawer && nav.isOpen;

  const panelRef = useRef<HTMLDivElement>(null);
  useDrawerKeyboard(panelRef, isDrawerOpen, nav.close);

  return (
    <div
      className={clsx(
        styles.nav,
        asDrawer && styles.drawer,
        isDrawerOpen && styles.open,
        !asDrawer && isFullScreenEnabled && styles.hidden,
        isCollapsed && styles.collapsed,
      )}
      aria-hidden={asDrawer && !isDrawerOpen}
    >
      {asDrawer ? <div className={styles.backdrop} onClick={nav.close} /> : null}
      <div
        ref={panelRef}
        className={styles.navPanel}
        role={asDrawer ? 'dialog' : undefined}
        aria-modal={asDrawer ? true : undefined}
        aria-label={asDrawer ? 'Navigation' : undefined}
      >
        {asDrawer ? (
          <div className={styles.closeRow}>
            <Button
              icon={<Icon name="close" />}
              onClick={nav.close}
              aria-label="Close navigation"
            />
          </div>
        ) : null}
        <NavCollapseContext.Provider value={asDrawer ? DRAWER_COLLAPSE_CONTEXT : collapseContext}>
          <MainNavigation
            collapsed={isCollapsed}
            topGroups={topGroups}
            bottomGroups={bottomGroups}
          />
        </NavCollapseContext.Provider>
      </div>
    </div>
  );
};

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

// Escape closes, Tab cycles within the panel, focus moves in on open and back out on close.
// Overlays opened from the nav (popovers, dialogs) mark Escape as handled when they close,
// so one keypress dismisses only the topmost layer.
const useDrawerKeyboard = (
  panelRef: RefObject<HTMLDivElement>,
  isOpen: boolean,
  close: () => void,
) => {
  useEffect(() => {
    const panel = panelRef.current;
    if (!isOpen || !panel) {
      return;
    }

    const opener = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const focusables = () => Array.from(panel.querySelectorAll<HTMLElement>(FOCUSABLE));
    focusables()[0]?.focus();

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (!e.defaultPrevented) {
          close();
        }
        return;
      }
      if (e.key !== 'Tab') {
        return;
      }
      const items = focusables();
      const first = items[0];
      const last = items[items.length - 1];
      if (!first || !last) {
        return;
      }
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('keydown', onKeyDown);
      opener?.focus();
    };
  }, [panelRef, isOpen, close]);
};
