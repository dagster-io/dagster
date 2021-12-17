import * as React from 'react';
import {Redirect, Route, Switch} from 'react-router-dom';

import {Page} from '../ui/Page';

import {InstanceBackfills} from './InstanceBackfills';
import {InstanceConfig} from './InstanceConfig';
import {InstanceHealthPage} from './InstanceHealthPage';
import {InstanceOverviewPage} from './InstanceOverviewPage';
import {InstanceSchedules} from './InstanceSchedules';
import {InstanceSensors} from './InstanceSensors';

export const InstanceStatusRoot = () => {
  return (
    <Page>
      <Switch>
        <Route path="/instance/overview" render={() => <InstanceOverviewPage />} />
        <Route path="/instance/health" render={() => <InstanceHealthPage />} />
        <Route path="/instance/schedules" render={() => <InstanceSchedules />} />
        <Route path="/instance/sensors" render={() => <InstanceSensors />} />
        <Route path="/instance/backfills" render={() => <InstanceBackfills />} />
        <Route path="/instance/config" render={() => <InstanceConfig />} />
        <Route path="*" render={() => <Redirect to="/instance" />} />
      </Switch>
    </Page>
  );
};
