import {Group, Spinner} from '@dagster-io/ui-components';
import clsx from 'clsx';

import styles from './css/LoadingOverlay.module.css';

export const LoadingOverlay = ({isLoading, message}: {isLoading: boolean; message: string}) => (
  <div className={clsx(styles.loadingOverlayContainer, !isLoading ? styles.hidden : null)}>
    <Group direction="row" spacing={8} alignItems="center">
      <Spinner purpose="body-text" />
      <div>{message}</div>
    </Group>
  </div>
);
