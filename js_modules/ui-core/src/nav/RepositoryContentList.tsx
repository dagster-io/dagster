import clsx from 'clsx';
import {ComponentProps} from 'react';
import {Link} from 'react-router-dom';

import styles from './css/RepositoryContentList.module.css';

interface ItemProps extends ComponentProps<typeof Link> {
  $active: boolean;
}

export const Item = ({$active, className, ...rest}: ItemProps) => (
  <Link
    className={clsx(styles.item, $active ? styles.itemActive : styles.itemInactive, className)}
    {...rest}
  />
);
