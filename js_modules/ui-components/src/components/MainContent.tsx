import clsx from 'clsx';
import {forwardRef} from 'react';

import styles from './css/MainContent.module.css';

export const MainContent = forwardRef<HTMLDivElement, React.ComponentPropsWithRef<'div'>>(
  ({className, ...props}, ref) => {
    return <div {...props} className={clsx(styles.mainContent, className)} ref={ref} />;
  },
);
