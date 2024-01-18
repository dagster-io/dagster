import * as React from 'react';
import styled from 'styled-components';

import {LEFT_NAV_WIDTH, LeftNav} from '../nav/LeftNav';
import {LayoutContext} from './LayoutProvider';

interface Props {
  banner?: React.ReactNode;
  children: React.ReactNode;
}

export const App = ({banner, children}: Props) => {
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
        <div>{banner}</div>
        <ChildContainer>{children}</ChildContainer>
      </Main>
    </Container>
  );
};

const Main = styled.div<{$smallScreen: boolean; $navOpen: boolean}>`
  height: 100%;
  z-index: 1;
  display: flex;
  flex-direction: column;

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

const ChildContainer = styled.div`
  height: 100%;
  overflow: hidden;
`;
