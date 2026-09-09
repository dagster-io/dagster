import {Box, DagsterIcon, DagsterLogo} from '@dagster-io/ui-components';
import clsx from 'clsx';
import {Link} from 'react-router-dom';

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
          <Box padding={8} className={clsx(styles.fullLogo, styles.brandLogo)}>
            <DagsterLogo height={28} />
          </Box>
          <Box padding={{vertical: 8}} className={clsx(styles.collapsedLogo, styles.brandLogo)}>
            <DagsterIcon height={28} />
          </Box>
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
