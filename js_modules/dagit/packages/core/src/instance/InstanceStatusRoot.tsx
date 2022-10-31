import {Page} from '@dagster-io/ui';
import * as React from 'react';
import {Redirect, Route, Switch} from 'react-router-dom';

import {InstanceConfig} from './InstanceConfig';
import {InstanceHealthPage} from './InstanceHealthPage';

const CodeLocationsPage = React.lazy(() => import('./CodeLocationsPage'));

export const InstanceStatusRoot = () => {
  return (
    <Page>
      <Switch>
        <Route path="/instance/health">
          <InstanceHealthPage />
        </Route>
        <Route path="/instance/config">
          <InstanceConfig />
        </Route>
        <Route path="/instance/code-locations">
          <React.Suspense fallback={<div />}>
            <CodeLocationsPage />
          </React.Suspense>
        </Route>
        <Route path="*" render={() => <Redirect to="/instance" />} />
      </Switch>
    </Page>
  );
};
