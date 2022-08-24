import {Page} from '@dagster-io/ui';
import * as React from 'react';
import {Redirect, Route, Switch} from 'react-router-dom';

import {InstanceBackfills} from './InstanceBackfills';
import {InstanceConfig} from './InstanceConfig';
import {InstanceHealthPage} from './InstanceHealthPage';
import {InstanceOverviewPage} from './InstanceOverviewPage';
import {InstanceSchedules} from './InstanceSchedules';
import {InstanceSensors} from './InstanceSensors';

const CodeLocationsPage = React.lazy(() => import('./CodeLocationsPage'));

export const InstanceStatusRoot = () => (
  <Page>
    <Switch>
      <Route path="/instance/overview">
        <InstanceOverviewPage />
      </Route>
      <Route path="/instance/health">
        <InstanceHealthPage />
      </Route>
      <Route path="/instance/schedules">
        <InstanceSchedules />
      </Route>
      <Route path="/instance/sensors">
        <InstanceSensors />
      </Route>
      <Route path="/instance/backfills">
        <InstanceBackfills />
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
