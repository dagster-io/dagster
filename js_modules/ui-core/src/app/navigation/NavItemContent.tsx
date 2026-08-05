import {Box} from '@dagster-io/ui-components';
import {ReactNode} from 'react';

import styles from './css/MainNavigation.module.css';

interface Props {
  icon: ReactNode;
  label?: string;
  collapsed: boolean;
  right?: ReactNode;
}

export const NavItemContent = ({icon, label, collapsed, right}: Props) => {
  if (collapsed) {
    return (
      <Box flex={{alignItems: 'center', justifyContent: 'center'}} padding={8}>
        <div>{icon}</div>
      </Box>
    );
  }

  return (
    <Box
      flex={{direction: 'row', alignItems: 'center', gap: 8}}
      padding={{vertical: 8, horizontal: 12}}
    >
      <div>{icon}</div>
      {label && <div className={styles.itemLabel}>{label}</div>}
      {right ? <div>{right}</div> : null}
    </Box>
  );
};
