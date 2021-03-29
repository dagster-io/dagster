import * as React from 'react';
import {Route, Switch} from 'react-router-dom';

import {InstanceRoot} from '../instance/InstanceRoot';
import {LeftNavBranch} from '../nav/LeftNavBranch';
import {AllSchedulesRoot} from '../schedules/AllSchedulesRoot';
import {AllSensorsRoot} from '../sensors/AllSensorsRoot';
import {AllPipelinesRoot} from '../workspace/AllPipelinesRoot';
import {WorkspaceRoot} from '../workspace/WorkspaceRoot';

import {FallthroughRoot} from './FallthroughRoot';
import {FeatureFlagsRoot} from './FeatureFlagsRoot';
import {SettingsRoot} from './SettingsRoot';

export const App = () => (
  <div style={{display: 'flex', height: '100%'}}>
    <LeftNavBranch />
    <Switch>
      <Route path="/flags" component={FeatureFlagsRoot} />
      <Route path="/instance" component={InstanceRoot} />
      <Route path="/workspace" component={WorkspaceRoot} />
      <Route path="/pipelines" component={AllPipelinesRoot} />
      <Route path="/schedules" component={AllSchedulesRoot} />
      <Route path="/sensors" component={AllSensorsRoot} />
      <Route path="/settings" component={SettingsRoot} />
      <Route path="*" component={FallthroughRoot} />
    </Switch>
  </div>
);
