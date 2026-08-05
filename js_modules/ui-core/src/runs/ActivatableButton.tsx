import {Button} from '@dagster-io/ui-components';
import clsx from 'clsx';
import {ComponentProps} from 'react';

import styles from './css/ActivatableButton.module.css';

export {styles as activatableButtonStyles};

type ActivatableButtonProps = {$active: boolean} & ComponentProps<typeof Button>;

export const ActivatableButton = ({$active, className, ...rest}: ActivatableButtonProps) => (
  <Button
    className={clsx(styles.activatableButton, $active ? styles.active : styles.inactive, className)}
    {...rest}
  />
);
