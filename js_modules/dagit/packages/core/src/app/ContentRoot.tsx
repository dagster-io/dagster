import * as React from 'react';
import {Route, Switch} from 'react-router-dom';

import {FallthroughRoot} from './FallthroughRoot';

const InstanceRoot = React.lazy(() => import('../instance/InstanceRoot'));
const SettingsRoot = React.lazy(() => import('../app/SettingsRoot'));
const WorkspaceRoot = React.lazy(() => import('../workspace/WorkspaceRoot'));

export const ContentRoot = React.memo(() => (
  <React.Suspense fallback={<div />}>
    <Switch>
      <Route path="/instance" component={InstanceRoot} />
      <Route path="/workspace" component={WorkspaceRoot} />
      <Route path="/settings" component={SettingsRoot} />
      <Route path="*" component={FallthroughRoot} />
    </Switch>
  </React.Suspense>
));
