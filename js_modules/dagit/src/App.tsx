import * as React from 'react';
import {BrowserRouter, Route, Switch} from 'react-router-dom';

import {CustomAlertProvider} from 'src/CustomAlertProvider';
import {CustomConfirmationProvider} from 'src/CustomConfirmationProvider';
import {CustomTooltipProvider} from 'src/CustomTooltipProvider';
import {APP_PATH_PREFIX} from 'src/DomUtils';
import {FallthroughRoot} from 'src/FallthroughRoot';
import {FeatureFlagsRoot} from 'src/FeatureFlagsRoot';
import {TimezoneProvider} from 'src/TimeComponents';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {InstanceRoot} from 'src/instance/InstanceRoot';
import {LeftNav} from 'src/nav/LeftNav';
import {WorkspaceContext, useWorkspaceState} from 'src/workspace/WorkspaceContext';
import {WorkspaceRoot} from 'src/workspace/WorkspaceRoot';

export const AppContent = () => {
  useDocumentTitle('Dagit');
  const workspaceState = useWorkspaceState();

  return (
    <div style={{display: 'flex', height: '100%'}}>
      <WorkspaceContext.Provider value={workspaceState}>
        <LeftNav />
        <CustomConfirmationProvider>
          <Switch>
            <Route path="/flags" component={FeatureFlagsRoot} />
            <Route path="/instance" component={InstanceRoot} />
            <Route path="/workspace" component={WorkspaceRoot} />
            <Route path="*" component={FallthroughRoot} />
          </Switch>
          <CustomTooltipProvider />
          <CustomAlertProvider />
        </CustomConfirmationProvider>
      </WorkspaceContext.Provider>
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
