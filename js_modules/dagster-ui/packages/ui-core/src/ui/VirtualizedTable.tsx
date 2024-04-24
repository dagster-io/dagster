import {Box} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

export const HeaderCell = ({
  children,
  style,
  onClick,
  ...rest
}: React.ComponentProps<typeof CellBox>) => {
  // no text select
  const clickStyle = onClick ? {cursor: 'pointer', userSelect: 'none'} : {};

  return (
    <CellBox
      padding={{vertical: 8, horizontal: 12}}
      border="right"
      style={{
        whiteSpace: 'nowrap',
        textOverflow: 'ellipsis',
        overflow: 'hidden',
        ...clickStyle,
        ...(style || {}),
      }}
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
}: {
  children?: React.ReactNode;
  style?: React.CSSProperties;
}) => (
  <CellBox
    padding={12}
    flex={{direction: 'column', justifyContent: 'flex-start'}}
    style={{overflow: 'hidden', ...(style || {})}}
    border="right"
  >
    {children}
  </CellBox>
);

const CellBox = styled(Box)`
  :first-child {
    padding-left: 24px;
  }

  :last-child {
    padding-right: 24px;
  }
`;

export const Container = styled.div`
  height: 100%;
  overflow: auto;
`;

type InnerProps = {
  $totalHeight: number;
};

export const Inner = styled.div.attrs<InnerProps>(({$totalHeight}) => ({
  style: {
    height: `${$totalHeight}px`,
  },
}))<InnerProps>`
  position: relative;
  width: 100%;
`;

type RowProps = {$height: number; $start: number};

export const Row = styled.div.attrs<RowProps>(({$height, $start}) => ({
  style: {
    height: `${$height}px`,
    transform: `translateY(${$start}px)`,
  },
}))<RowProps>`
  left: 0;
  position: absolute;
  right: 0;
  top: 0;
  overflow: hidden;
`;

type DynamicRowContainerProps = {$start: number};

export const DynamicRowContainer = styled.div.attrs<DynamicRowContainerProps>(({$start}) => ({
  style: {
    transform: `translateY(${$start}px)`,
  },
}))<DynamicRowContainerProps>`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
`;
