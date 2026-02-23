import clsx from 'clsx';
import {Link} from 'react-router-dom';

import {DaggyLogo} from '../../../app/navigation/DaggyLogo';
import {DaggyWordmark} from '../../../app/navigation/DaggyWordmark';
import {NavigationGroupDisplay} from '../../../app/navigation/NavigationGroupDisplay';
import styles from '../../../app/navigation/css/MainNavigation.module.css';
import {NavigationGroup} from '../../../app/navigation/types';

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
