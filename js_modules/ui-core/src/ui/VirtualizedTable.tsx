import {Box, Colors} from '@dagster-io/ui-components';
import clsx from 'clsx';
import * as React from 'react';

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
    style={{
      display: 'grid',
      gridTemplateColumns: templateColumns,
      height: TABLE_HEADER_HEIGHT,
      fontSize: '12px',
      color: Colors.textLight(),
      ...(sticky
        ? {
            position: 'sticky',
            top: 0,
            zIndex: 1,
            background: Colors.backgroundDefault(),
          }
        : {}),
    }}
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
    style={{...(style || {})}}
    border="right"
    className={className}
  >
    {children}
  </CellBox>
);

export const Container = React.forwardRef(
  (
    {className, children, style, ...rest}: React.HTMLAttributes<HTMLDivElement>,
    ref: React.ForwardedRef<HTMLDivElement>,
  ) => (
    <div className={clsx(styles.container, className)} style={style} ref={ref} {...rest}>
      {children}
    </div>
  ),
);

export const Inner = React.forwardRef(
  (
    {
      $totalHeight,
      children,
      className,
      ...rest
    }: {
      $totalHeight: number;
      children?: React.ReactNode;
      className?: string;
    } & React.HTMLAttributes<HTMLDivElement>,
    ref: React.ForwardedRef<HTMLDivElement>,
  ) => (
    <div
      className={clsx(styles.inner, className)}
      style={{height: `${$totalHeight}px`}}
      ref={ref}
      {...rest}
    >
      {children}
    </div>
  ),
);

export const Row = React.forwardRef(
  (
    {
      $height,
      $start,
      children,
      className,
      ...rest
    }: {
      $height: number;
      $start: number;
      children?: React.ReactNode;
      className?: string;
    } & React.HTMLAttributes<HTMLDivElement>,
    ref: React.ForwardedRef<HTMLDivElement>,
  ) => (
    <div
      className={clsx(styles.row, className)}
      style={{height: `${$height}px`, transform: `translateY(${$start}px)`}}
      ref={ref}
      {...rest}
    >
      {children}
    </div>
  ),
);
