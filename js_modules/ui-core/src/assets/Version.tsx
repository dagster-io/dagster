import clsx from 'clsx';
import * as React from 'react';

import styles from './css/Version.module.css';

export const Version = React.forwardRef<HTMLDivElement, React.ComponentPropsWithoutRef<'div'>>(
  (props, ref) => {
    return <div {...props} ref={ref} className={clsx(styles.version, props.className)} />;
  },
);
