import clsx from 'clsx';

import {DaggyWordmarkDarkMode} from './DaggyWordmarkDarkMode';
import {DaggyWordmarkLightMode} from './DaggyWordmarkLightMode';
import styles from './css/DaggyLogo.module.css';

export const DaggyWordmark = () => {
  return (
    <div className={clsx(styles.daggyContainer, styles.daggyWordmarkContainer)}>
      <div className={styles.daggyLightMode}>
        <DaggyWordmarkLightMode />
      </div>
      <div className={styles.daggyDarkMode}>
        <DaggyWordmarkDarkMode />
      </div>
    </div>
  );
};
