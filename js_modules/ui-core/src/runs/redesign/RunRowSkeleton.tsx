import {Skeleton} from '@dagster-io/ui-components';

import styles from './css/RunRowSkeleton.module.css';

export const RunRowSkeleton = () => (
  <div className={styles.row}>
    <Skeleton $height={24} $width="min(640px, 100%)" />
  </div>
);
