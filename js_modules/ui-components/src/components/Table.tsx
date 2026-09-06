import clsx from 'clsx';
import {type TableHTMLAttributes} from 'react';

import styles from './css/Table.module.css';

export interface TableProps extends TableHTMLAttributes<HTMLTableElement> {
  compact?: boolean;
}

export const TABLE_CLASS = 'tableGlobal';

export const Table = ({compact, className, ...props}: TableProps) => (
  <table
    cellPadding="0"
    cellSpacing="0"
    className={clsx(TABLE_CLASS, styles.table, compact && styles.compact, className)}
    {...props}
  />
);
