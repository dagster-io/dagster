import clsx from 'clsx';
import {CSSProperties, useCallback, useContext} from 'react';

import {LayoutContext} from './LayoutProvider';
import {LEFT_NAV_WIDTH, LeftNav} from '../nav/LeftNav';
import {useFullScreen} from './AppTopNav/AppTopNavContext';
import styles from './css/App.module.css';

interface Props {
  banner?: React.ReactNode;
  children: React.ReactNode;
}

export const App = ({banner, children}: Props) => {
  const {nav} = useContext(LayoutContext);

  const onClickMain = useCallback(() => {
    if (nav.isSmallScreen) {
      nav.close();
    }
  }, [nav]);

  const {isFullScreen} = useFullScreen();

  return (
    <div
      className={clsx(styles.container, isFullScreen ? styles.fullScreen : null)}
      style={{'--left-nav-width': `${LEFT_NAV_WIDTH}px`} as CSSProperties}
    >
      <LeftNav />
      <div
        className={clsx(styles.main, nav.isSmallScreen || !nav.isOpen ? styles.hideNav : null)}
        onClick={onClickMain}
      >
        <div>{banner}</div>
        <div className={styles.childContainer}>{children}</div>
      </div>
    </div>
  );
};
