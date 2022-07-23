import * as React from 'react';
import {Route, Switch} from 'react-router-dom';

const InstanceRoot = React.lazy(() => import('../instance/InstanceRoot'));
const UserSettingsRoot = React.lazy(() => import('./UserSettingsRoot'));
const WorkspaceRoot = React.lazy(() => import('../workspace/WorkspaceRoot'));
const FallthroughRoot = React.lazy(() => import('./FallthroughRoot'));

export const ContentRoot = React.memo(() => (
  <Switch>
    <Route path="/instance">
      <React.Suspense fallback={<div />}>
        <InstanceRoot />
      </React.Suspense>
    </Route>
    <Route path="/workspace">
      <React.Suspense fallback={<div />}>
        <WorkspaceRoot />
      </React.Suspense>
    </Route>
    <Route path="/settings">
      <React.Suspense fallback={<div />}>
        <UserSettingsRoot />
      </React.Suspense>
    </Route>
    <Route path="*">
      <React.Suspense fallback={<div />}>
        <FallthroughRoot />
      </React.Suspense>
    </Route>
  </Switch>
));
