import * as React from 'react';
import {BrowserRouter, Route, Switch} from 'react-router-dom';

import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {InstanceRoot} from '../instance/InstanceRoot';
import {LeftNavBranch} from '../nav/LeftNavBranch';
import {AllSchedulesRoot} from '../schedules/AllSchedulesRoot';
import {AllSensorsRoot} from '../sensors/AllSensorsRoot';
import {AllPipelinesRoot} from '../workspace/AllPipelinesRoot';
import {WorkspaceProvider} from '../workspace/WorkspaceContext';
import {WorkspaceRoot} from '../workspace/WorkspaceRoot';

import {CustomAlertProvider} from './CustomAlertProvider';
import {CustomConfirmationProvider} from './CustomConfirmationProvider';
import {CustomTooltipProvider} from './CustomTooltipProvider';
import {APP_PATH_PREFIX} from './DomUtils';
import {FallthroughRoot} from './FallthroughRoot';
import {FeatureFlagsRoot} from './FeatureFlagsRoot';
import {SettingsRoot} from './SettingsRoot';
import {TimezoneProvider} from './time/TimezoneContext';

export const AppContent = () => {
  useDocumentTitle('Dagit');
  return (
    <div style={{display: 'flex', height: '100%'}}>
      <WorkspaceProvider>
        <LeftNavBranch />
        <CustomConfirmationProvider>
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
          <CustomTooltipProvider />
          <CustomAlertProvider />
        </CustomConfirmationProvider>
      </WorkspaceProvider>
    </div>
  );
};

export const App = () => (
  <BrowserRouter basename={APP_PATH_PREFIX}>
    <TimezoneProvider>
      <AppContent />
    </TimezoneProvider>
  </BrowserRouter>
);
