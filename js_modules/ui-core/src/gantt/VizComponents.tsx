import clsx from 'clsx';
import * as React from 'react';

import styles from './css/VizComponents.module.css';

export const OptionsContainer = React.forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<'div'>
>((props, ref) => {
  return <div {...props} ref={ref} className={clsx(styles.optionsContainer, props.className)} />;
});

export const OptionsDivider = React.forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<'div'>
>((props, ref) => {
  return <div {...props} ref={ref} className={clsx(styles.optionsDivider, props.className)} />;
});

export const OptionsSpacer = React.forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<'div'>
>((props, ref) => {
  return <div {...props} ref={ref} className={clsx(styles.optionsSpacer, props.className)} />;
});
