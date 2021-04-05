import * as React from 'react';
import {Route, Switch} from 'react-router-dom';
import styled from 'styled-components/macro';

import {InstanceRoot} from '../instance/InstanceRoot';
import {LeftNav} from '../nav/LeftNav';
import {AllSchedulesRoot} from '../schedules/AllSchedulesRoot';
import {AllSensorsRoot} from '../sensors/AllSensorsRoot';
import {WorkspaceRoot} from '../workspace/WorkspaceRoot';

import {FallthroughRoot} from './FallthroughRoot';
import {FeatureFlagsRoot} from './FeatureFlagsRoot';
import {LayoutContext} from './LayoutProvider';

const ContentRoot = React.memo(() => (
  <Switch>
    <Route path="/flags" component={FeatureFlagsRoot} />
    <Route path="/instance" component={InstanceRoot} />
    <Route path="/workspace" component={WorkspaceRoot} />
    <Route path="/schedules" component={AllSchedulesRoot} />
    <Route path="/sensors" component={AllSensorsRoot} />
    <Route path="*" component={FallthroughRoot} />
  </Switch>
));

export const App = () => {
  const {nav} = React.useContext(LayoutContext);

  const onClickMain = React.useCallback(() => {
    nav.close();
  }, [nav]);

  return (
    <Container>
      <LeftNav />
      <Main $navOpen={nav.isOpen} onClick={onClickMain}>
        <ContentRoot />
      </Main>
    </Container>
  );
};

const Main = styled.div<{$navOpen: boolean}>`
  height: 100%;
  width: 100%;

  @media (max-width: 2560px) {
    margin-left: 280px;
    width: calc(100% - 280px);
  }

  @media (max-width: 1440px) {
    margin-left: 0;
    width: 100%;
  }
`;

const Container = styled.div`
  display: flex;
  height: calc(100% - 50px);
`;
