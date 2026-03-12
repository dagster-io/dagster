import clsx from 'clsx';
import {forwardRef} from 'react';

import styles from './css/Page.module.css';

export const Page = forwardRef<HTMLDivElement, React.ComponentPropsWithRef<'div'>>(
  ({className, ...props}, ref) => {
    return <div {...props} className={clsx(styles.page, className)} ref={ref} />;
  },
);
