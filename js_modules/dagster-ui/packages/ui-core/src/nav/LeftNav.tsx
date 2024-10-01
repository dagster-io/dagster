import {Colors} from '@dagster-io/ui-components';
import {useContext, useRef} from 'react';
import styled from 'styled-components';

import {LeftNavRepositorySection} from './LeftNavRepositorySection';
import {LayoutContext} from '../app/LayoutProvider';

export const LeftNav = () => {
  const {nav} = useContext(LayoutContext);

  const wasEverOpen = useRef(nav.isOpen);
  if (nav.isOpen) {
    wasEverOpen.current = true;
  }

  return (
    <LeftNavContainer $open={nav.isOpen}>
      {wasEverOpen.current ? <LeftNavRepositorySection /> : null}
    </LeftNavContainer>
  );
};

export const LEFT_NAV_WIDTH = 332;

const LeftNavContainer = styled.div<{$open: boolean}>`
  position: fixed;
  z-index: 2;
  top: 64px;
  bottom: 0;
  left: 0;
  width: ${LEFT_NAV_WIDTH}px;
  display: flex;
  flex-shrink: 0;
  flex-direction: column;
  justify-content: start;
  background: ${Colors.backgroundDefault()};
  box-shadow: 1px 0px 0px ${Colors.keylineDefault()};
  transform: translateX(${({$open}) => ($open ? '0' : `-${LEFT_NAV_WIDTH}px`)});
  transition: transform 150ms ease-in-out;
`;
