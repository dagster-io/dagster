import * as React from 'react';
import styled from 'styled-components/macro';

import {LeftNav, LEFT_NAV_WIDTH} from '../nav/LeftNav';

import {LayoutContext} from './LayoutProvider';

export const App: React.FC = (props) => {
  const {nav} = React.useContext(LayoutContext);

  const onClickMain = React.useCallback(() => {
    if (nav.isSmallScreen) {
      nav.close();
    }
  }, [nav]);

  return (
    <Container>
      <LeftNav />
      <Main $smallScreen={nav.isSmallScreen} $navOpen={nav.isOpen} onClick={onClickMain}>
        {props.children}
      </Main>
    </Container>
  );
};

const Main = styled.div<{$smallScreen: boolean; $navOpen: boolean}>`
  height: 100%;
  z-index: 1;

  ${({$navOpen, $smallScreen}) => {
    if ($smallScreen || !$navOpen) {
      return `
        margin-left: 0;
        width: 100%;
      `;
    }

    return `
      margin-left: ${LEFT_NAV_WIDTH}px;
      width: calc(100% - ${LEFT_NAV_WIDTH}px);
    `;
  }}
`;

const Container = styled.div`
  display: flex;
  height: calc(100% - 64px);
`;
