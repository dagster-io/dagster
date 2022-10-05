import * as React from 'react';
import {Redirect, Route, Switch} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {InstanceBackfills} from '../instance/InstanceBackfills';
import {InstanceSchedules} from '../instance/InstanceSchedules';
import {InstanceSensors} from '../instance/InstanceSensors';

import {OverviewTimelineRoot} from './OverviewTimelineRoot';

export const OverviewRoot = () => {
  const {flagNewWorkspace} = useFeatureFlags();

  if (!flagNewWorkspace) {
    return <Redirect to="/instance/overview" />;
  }

  return (
    <Switch>
      <Route path="/overview/timeline">
        <OverviewTimelineRoot />
      </Route>
      <Route path="/overview/schedules">
        <InstanceSchedules />
      </Route>
      <Route path="/overview/sensors">
        <InstanceSensors />
      </Route>
      <Route path="/overview/backfills">
        <InstanceBackfills />
      </Route>
      <Route path="*" render={() => <Redirect to="/overview/timeline" />} />
    </Switch>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default OverviewRoot;
