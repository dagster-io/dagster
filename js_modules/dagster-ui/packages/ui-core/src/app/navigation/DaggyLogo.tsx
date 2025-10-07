import {DaggyLogoDarkMode} from './DaggyLogoDarkMode';
import {DaggyLogoLightMode} from './DaggyLogoLightMode';
import styles from './css/DaggyLogo.module.css';

export const DaggyLogo = () => {
  return (
    <div className={styles.daggyContainer}>
      <div className={styles.daggyLightMode}>
        <DaggyLogoLightMode />
      </div>
      <div className={styles.daggyDarkMode}>
        <DaggyLogoDarkMode />
      </div>
    </div>
  );
};
