import clsx from 'clsx';

import styles from './IndeterminateLoadingBar.module.css';

export const IndeterminateLoadingBar = ({
  $loading,
  $height = 2,
  style,
}: {
  $loading: boolean | undefined;
  $height?: number;
  style?: React.CSSProperties;
}) => {
  return (
    <div
      className={clsx(styles.loadingBar, $loading && styles.loading)}
      style={{...style, '--height': `${$height}px`} as React.CSSProperties}
    />
  );
};
