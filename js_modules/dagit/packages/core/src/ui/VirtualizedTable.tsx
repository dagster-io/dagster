import {Box, Colors} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

export const HeaderCell: React.FC = ({children}) => (
  <Box
    padding={{vertical: 8, horizontal: 24}}
    border={{side: 'right', width: 1, color: Colors.KeylineGray}}
    style={{whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden'}}
  >
    {children}
  </Box>
);

export const RowCell: React.FC = ({children}) => (
  <Box
    padding={{horizontal: 24}}
    flex={{direction: 'column', justifyContent: 'center'}}
    style={{color: Colors.Gray500, overflow: 'hidden'}}
    border={{side: 'right', width: 1, color: Colors.KeylineGray}}
  >
    {children}
  </Box>
);

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
