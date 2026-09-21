import clsx from 'clsx';
import * as React from 'react';

import styles from './css/SessionSettingsBar.module.css';

export const SessionSettingsBar = React.forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<'div'>
>((props, ref) => {
  return <div {...props} ref={ref} className={clsx(styles.sessionSettingsBar, props.className)} />;
});
