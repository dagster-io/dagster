import clsx from 'clsx';
import {Link} from 'react-router-dom';

import {DaggyLogo} from './DaggyLogo';
import {DaggyWordmark} from './DaggyWordmark';
import {NavigationGroupDisplay} from './NavigationGroupDisplay';
import styles from './css/MainNavigation.module.css';
import {NavigationGroup} from './types';

interface Props {
  collapsed: boolean;
  topGroups: NavigationGroup[];
  bottomGroups: NavigationGroup[];
}

export const MainNavigation = ({collapsed, topGroups, bottomGroups}: Props) => {
  return (
    <nav className={clsx(styles.nav, collapsed && styles.collapsed)}>
      <div className={styles.logoContainer}>
        <Link to="/">
          <div className={styles.fullLogo}>
            <DaggyWordmark />
          </div>
          <div className={styles.collapsedLogo}>
            <DaggyLogo />
          </div>
        </Link>
      </div>
      <NavigationGroupDisplay list={topGroups} className={styles.topGroups} collapsed={collapsed} />
      <NavigationGroupDisplay
        list={bottomGroups}
        className={styles.bottomGroups}
        collapsed={collapsed}
      />
    </nav>
  );
};
