import {Colors} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import {LayoutContext} from '../app/LayoutProvider';

import {LeftNavRepositorySection} from './LeftNavRepositorySection';

export const LeftNav = () => {
  const {nav} = React.useContext(LayoutContext);

  return (
    <LeftNavContainer $open={nav.isOpen} $smallScreen={nav.isSmallScreen}>
      <LeftNavRepositorySection />
    </LeftNavContainer>
  );
};

export const LEFT_NAV_WIDTH = 332;

const LeftNavContainer = styled.div<{$open: boolean; $smallScreen: boolean}>`
  position: fixed;
  z-index: 2;
  top: 64px;
  bottom: 0;
  left: 0;
  padding-top: 16px;
  width: ${LEFT_NAV_WIDTH}px;
  display: ${({$open, $smallScreen}) => ($open || $smallScreen ? 'flex' : 'none')};
  flex-shrink: 0;
  flex-direction: column;
  justify-content: start;
  background: ${Colors.Gray100};
  box-shadow: 1px 0px 0px ${Colors.KeylineGray};

  ${(p) =>
    p.$smallScreen
      ? `
        transform: translateX(${p.$open ? '0' : `-${LEFT_NAV_WIDTH}px`});
        transition: transform 150ms ease-in-out;
      `
      : ``}
`;
