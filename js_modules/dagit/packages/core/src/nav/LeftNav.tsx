import * as React from 'react';
import styled from 'styled-components/macro';

import {LayoutContext} from '../app/LayoutProvider';
import {ColorsWIP} from '../ui/Colors';

import {LeftNavRepositorySection} from './LeftNavRepositorySection';

export const LeftNav = () => {
  const {nav} = React.useContext(LayoutContext);

  return (
    <LeftNavContainer $open={nav.isOpen}>
      <LeftNavRepositorySection />
    </LeftNavContainer>
  );
};

const LeftNavContainer = styled.div<{$open: boolean}>`
  position: fixed;
  z-index: 2;
  top: 64px;
  bottom: 0;
  left: 0;
  padding-top: 16px;
  width: 332px;
  display: flex;
  flex-shrink: 0;
  flex-direction: column;
  justify-content: start;
  background: ${ColorsWIP.Gray100};
  box-shadow: 1px 0px 0px ${ColorsWIP.KeylineGray};

  @media (max-width: 1440px) {
    transform: translateX(${({$open}) => ($open ? '0' : '-332px')});
    transition: transform 150ms ease-in-out;
  }
`;
