// eslint-disable-next-line no-restricted-imports
import {HTMLTable, HTMLTableProps} from '@blueprintjs/core';
import clsx from 'clsx';

import styles from './css/Table.module.css';

export interface TableProps extends HTMLTableProps {
  compact?: boolean;
}

export const TABLE_CLASS = 'tableGlobal';

export const Table = ({compact, className, ...props}: TableProps) => (
  <HTMLTable
    className={clsx(TABLE_CLASS, styles.table, compact && styles.compact, className)}
    {...props}
  />
);
