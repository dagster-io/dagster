import clsx from 'clsx';

import styles from './css/IndeterminateLoadingBar.module.css';

export const IndeterminateLoadingBar = ({
  $loading,
  style,
}: {
  $loading: boolean | undefined;
  style?: React.CSSProperties;
}) => {
  return <div className={clsx(styles.loadingBar, $loading && styles.loading)} style={style} />;
};
