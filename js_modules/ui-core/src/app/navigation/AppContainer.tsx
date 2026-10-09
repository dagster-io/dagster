import clsx from 'clsx';
import {ReactNode} from 'react';

import {MobileNavButton} from './MobileNavButton';
import {NavPanel} from './NavPanel';
import styles from './css/AppContainer.module.css';
import './css/MobileLayout.css';
import {NavigationGroup} from './types';
import {IsMobileContext} from '../layout/IsMobileContext';
import {useIsMobileLayout} from '../layout/LayoutMode';
import {MobileDesktopFallbackBanner} from '../layout/MobileDesktopFallback';
import {useMobileRouteEnabled} from '../layout/mobileRouteStatus';

interface Props {
  topGroups: NavigationGroup[];
  bottomGroups: NavigationGroup[];
  banner?: ReactNode;
  isFullScreenEnabled?: boolean;
  children: ReactNode;
}

/**
 * The app frame: the main navigation beside (desktop) or over (mobile) the page.
 *
 * The element structure is the same in both modes so that the nav and the page never
 * remount when the mode changes — see `NavPanel`.
 */
export const AppContainer = (props: Props) => {
  const {topGroups, bottomGroups, banner, children, isFullScreenEnabled = false} = props;

  // `isMobile`: the app booted in mobile layout mode (a phone). `isMobileRouteEnabled`:
  // additionally, the current route supports mobile. A phone on an unsupported route gets
  // the desktop navigation at desktop width plus a fallback banner.
  const isMobile = useIsMobileLayout();
  const isMobileRouteEnabled = useMobileRouteEnabled();

  return (
    <IsMobileContext.Provider value={isMobileRouteEnabled}>
      <div className={clsx(styles.container, isMobileRouteEnabled && styles.mobile)}>
        <NavPanel
          asDrawer={isMobileRouteEnabled}
          isFullScreenEnabled={isFullScreenEnabled}
          topGroups={topGroups}
          bottomGroups={bottomGroups}
        />
        <div
          className={clsx(
            styles.main,
            !isMobileRouteEnabled && isFullScreenEnabled && styles.fullScreen,
          )}
        >
          <div>
            {isMobile && !isMobileRouteEnabled ? <MobileDesktopFallbackBanner /> : null}
            {banner}
          </div>
          <div className={styles.child}>{children}</div>
          {isMobileRouteEnabled && !isFullScreenEnabled ? <MobileNavButton /> : null}
        </div>
      </div>
    </IsMobileContext.Provider>
  );
};
