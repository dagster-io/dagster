import * as React from 'react';
import {Redirect, Route, Switch} from 'react-router-dom';

import {InstanceBackfills} from '../instance/InstanceBackfills';
import {BackfillPage} from '../instance/backfill/BackfillPage';

import {OverviewJobsRoot} from './OverviewJobsRoot';
import {OverviewResourcesRoot} from './OverviewResourcesRoot';
import {OverviewSchedulesRoot} from './OverviewSchedulesRoot';
import {OverviewSensorsRoot} from './OverviewSensorsRoot';
import {OverviewTimelineRoot} from './OverviewTimelineRoot';

export const OverviewRoot = () => {
  return (
    <Switch>
      <Route path="/overview/timeline">
        <OverviewTimelineRoot />
      </Route>
      <Route path="/overview/jobs">
        <OverviewJobsRoot />
      </Route>
      <Route path="/overview/schedules">
        <OverviewSchedulesRoot />
      </Route>
      <Route path="/overview/sensors">
        <OverviewSensorsRoot />
      </Route>
      <Route path="/overview/backfills/:backfillId">
        <BackfillPage />
      </Route>
      <Route path="/overview/backfills" exact>
        <InstanceBackfills />
      </Route>
      <Route path="/overview/resources">
        <OverviewResourcesRoot />
      </Route>
      <Route path="*" render={() => <Redirect to="/overview/timeline" />} />
    </Switch>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default OverviewRoot;
