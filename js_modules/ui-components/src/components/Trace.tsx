import clsx from 'clsx';
import {forwardRef} from 'react';

import styles from './css/Trace.module.css';

export const Trace = forwardRef<HTMLDivElement, React.ComponentPropsWithRef<'div'>>(
  ({className, ...props}, ref) => {
    return <div {...props} className={clsx(styles.trace, className)} ref={ref} />;
  },
);
