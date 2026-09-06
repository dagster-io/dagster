import clsx from 'clsx';
import * as React from 'react';

import styles from './css/Code.module.css';

export const Code = ({className, ...props}: React.HTMLAttributes<HTMLElement>) => (
  <code className={clsx(styles.code, className)} {...props} />
);
