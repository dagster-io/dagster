import clsx from 'clsx';
import * as React from 'react';

import {Box} from './Box';
import styles from './css/VirtualizedTable.module.css';

export const TABLE_HEADER_HEIGHT = 32;

export const HeaderRow = ({
  children,
  templateColumns,
  sticky = false,
}: {
  children: React.ReactNode;
  templateColumns: string;
  sticky?: boolean;
}) => (
  <Box
    border="top-and-bottom"
    className={clsx(styles.headerRow, sticky && styles.headerRowSticky)}
    style={{gridTemplateColumns: templateColumns}}
  >
    {children}
  </Box>
);

export const CellBox = ({className, ...rest}: React.ComponentProps<typeof Box>) => (
  <Box className={clsx(styles.cellBox, className)} {...rest} />
);

export const HeaderCell = ({
  children,
  className,
  onClick,
  ...rest
}: React.ComponentProps<typeof CellBox>) => {
  return (
    <CellBox
      padding={{vertical: 8, horizontal: 12}}
      border="right"
      className={clsx(styles.headerCell, onClick && styles.headerCellClickable, className)}
      onClick={onClick}
      {...rest}
    >
      {children}
    </CellBox>
  );
};

export const RowCell = ({
  children,
  style,
  className,
}: {
  children?: React.ReactNode;
  style?: React.CSSProperties;
  className?: string;
}) => (
  <CellBox
    padding={12}
    flex={{direction: 'column', justifyContent: 'flex-start'}}
    style={style}
    border="right"
    className={className}
  >
    {children}
  </CellBox>
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

export const Inner = React.forwardRef<
  HTMLDivElement,
  InnerProps & React.HTMLAttributes<HTMLDivElement>
>(({totalHeight, children, className, ...rest}, ref) => (
  <div
    className={clsx(styles.inner, className)}
    style={{height: `${totalHeight}px`}}
    ref={ref}
    {...rest}
  >
    {children}
  </div>
));

export type RowProps = {
  // Omit to let the row take its natural height (e.g. dynamic measurement via a
  // virtualizer's `measureElement`); pass it for fixed-height virtualization.
  height?: number;
  start: number;
  children?: React.ReactNode;
};

export const Row = React.forwardRef<
  HTMLDivElement,
  RowProps & React.HTMLAttributes<HTMLDivElement>
>(({height, start, children, className, style, ...rest}, ref) => (
  <div
    ref={ref}
    className={clsx(styles.row, className)}
    style={{
      ...(height === undefined ? {} : {height: `${height}px`}),
      transform: `translateY(${start}px)`,
      ...style,
    }}
    {...rest}
  >
    {children}
  </div>
));
