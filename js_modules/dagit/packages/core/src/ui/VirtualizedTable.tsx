import {Box, Colors} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

export const HeaderCell = ({children}: {children?: React.ReactNode}) => (
  <CellBox
    padding={{vertical: 8, horizontal: 12}}
    border={{side: 'right', width: 1, color: Colors.KeylineGray}}
    style={{whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden'}}
  >
    {children}
  </CellBox>
);

export const RowCell = ({children}: {children?: React.ReactNode}) => (
  <CellBox
    padding={12}
    flex={{direction: 'column', justifyContent: 'flex-start'}}
    style={{color: Colors.Gray500, overflow: 'hidden'}}
    border={{side: 'right', width: 1, color: Colors.KeylineGray}}
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
