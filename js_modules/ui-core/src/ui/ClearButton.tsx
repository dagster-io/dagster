import clsx from 'clsx';
import * as React from 'react';

import styles from './css/ClearButton.module.css';

export const ClearButton = React.forwardRef<
  HTMLButtonElement,
  React.ComponentPropsWithoutRef<'button'>
>((props, ref) => {
  return <button {...props} ref={ref} className={clsx(styles.clearButton, props.className)} />;
});
