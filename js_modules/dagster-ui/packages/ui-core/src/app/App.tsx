import * as React from 'react';
import styled from 'styled-components';

import {useFeatureFlags} from './Flags';
import {LayoutContext} from './LayoutProvider';
import {LEFT_NAV_WIDTH, LeftNav} from '../nav/LeftNav';

interface Props {
  banner?: React.ReactNode;
  children: React.ReactNode;
}

export const App = ({banner, children}: Props) => {
  const {nav} = React.useContext(LayoutContext);
  const {flagSettingsPage} = useFeatureFlags();

  const onClickMain = React.useCallback(() => {
    if (nav.isSmallScreen) {
      nav.close();
    }
  }, [nav]);

  return (
    <Container>
      {flagSettingsPage ? null : <LeftNav />}
      <Main
        $smallScreen={nav.isSmallScreen}
        $navOpen={nav.isOpen && !flagSettingsPage}
        onClick={onClickMain}
      >
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
