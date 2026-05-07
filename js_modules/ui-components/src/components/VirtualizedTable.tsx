import clsx from 'clsx';
import * as React from 'react';

import {Box} from './Box';
import styles from './css/VirtualizedTable.module.css';

export const HeaderCell = ({children}: {children?: React.ReactNode}) => (
  <Box
    className={styles.cellBox}
    padding={{vertical: 8, horizontal: 12}}
    border="right"
    style={{whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden'}}
  >
    {children}
  </Box>
);

export const RowCell = ({children}: {children?: React.ReactNode}) => (
  <Box
    className={styles.cellBox}
    padding={12}
    flex={{direction: 'column', justifyContent: 'flex-start'}}
    style={{overflow: 'hidden'}}
    border="right"
  >
    {children}
  </Box>
);

export const Container = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({className, ...props}, ref) => (
    <div ref={ref} className={clsx(styles.container, className)} {...props} />
  ),
);

export type InnerProps = {
  totalHeight: number;
  children?: React.ReactNode;
};

export const Inner = ({
  totalHeight,
  className,
  ...props
}: InnerProps & React.HTMLAttributes<HTMLDivElement>) => (
  <div className={clsx(styles.inner, className)} style={{height: `${totalHeight}px`}} {...props} />
);

export type RowProps = {height: number; start: number; children?: React.ReactNode};

export const Row = ({
  height,
  start,
  className,
  style,
  ...props
}: RowProps & React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={clsx(styles.row, className)}
    style={{height: `${height}px`, transform: `translateY(${start}px)`, ...style}}
    {...props}
  />
);
