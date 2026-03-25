import clsx from 'clsx';
import {ComponentProps} from 'react';

import {Tag} from './Tag';
import styles from './css/RadioTag.module.css';

interface RadioTagProps extends Omit<ComponentProps<typeof Tag>, 'intent'> {
  selected?: boolean;
}

export const RadioTag = ({selected = false, ...rest}: RadioTagProps) => {
  return (
    <span className={clsx(styles.wrapper, selected && styles.selected)}>
      <Tag intent={selected ? 'primary' : 'none'} {...rest} />
    </span>
  );
};
