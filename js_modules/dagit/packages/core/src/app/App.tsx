import * as React from 'react';
import {Route, Switch} from 'react-router-dom';
import styled from 'styled-components/macro';

import {LeftNav} from '../nav/LeftNav';

import {FallthroughRoot} from './FallthroughRoot';
import {LayoutContext} from './LayoutProvider';

const InstanceRoot = React.lazy(() => import('../instance/InstanceRoot'));
const SettingsRoot = React.lazy(() => import('../app/SettingsRoot'));
const WorkspaceRoot = React.lazy(() => import('../workspace/WorkspaceRoot'));

const ContentRoot = React.memo(() => (
  <React.Suspense fallback={<div />}>
    <Switch>
      <Route path="/instance" component={InstanceRoot} />
      <Route path="/workspace" component={WorkspaceRoot} />
      <Route path="/settings" component={SettingsRoot} />
      <Route path="*" component={FallthroughRoot} />
    </Switch>
  </React.Suspense>
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
  margin-left: 280px;
  width: calc(100% - 280px);

  @media (max-width: 1440px) {
    margin-left: 0;
    width: 100%;
  }
`;

const Container = styled.div`
  display: flex;
  height: calc(100% - 48px);
`;
