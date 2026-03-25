// eslint-disable-next-line no-restricted-imports
import {Radio as BlueprintRadio} from '@blueprintjs/core';
import clsx from 'clsx';
import * as React from 'react';

import styles from './css/Radio.module.css';

// Re-export Radio from Blueprint so that we don't have to deal with the lint
// error elsewhere.
export const Radio = BlueprintRadio;

export const RadioContainer = ({
  children,
  className,
  ...rest
}: React.ComponentPropsWithRef<'div'>) => (
  <div {...rest} className={clsx(styles.radioContainer, className)}>
    {children}
  </div>
);
