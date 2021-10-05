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
  width: 280px;
  display: flex;
  flex-shrink: 0;
  flex-direction: column;
  justify-content: start;
  background: ${ColorsWIP.Gray900};
  border-right: 1px solid ${ColorsWIP.Gray700};

  @media (max-width: 1440px) {
    box-shadow: 2px 0px 0px ${ColorsWIP.Gray200};
    transform: translateX(${({$open}) => ($open ? '0' : '-280px')});
    transition: transform 150ms ease-in-out;
  }
`;
