import {Redirect, Switch} from 'react-router-dom';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {OverviewActivityRoot} from './OverviewActivityRoot';
import {OverviewJobsRoot} from './OverviewJobsRoot';
import {OverviewResourcesRoot} from './OverviewResourcesRoot';
import {OverviewSchedulesRoot} from './OverviewSchedulesRoot';
import {OverviewSensorsRoot} from './OverviewSensorsRoot';
import {featureEnabled, useFeatureFlags} from '../app/Flags';
import {Route} from '../app/Route';
import {useAutoMaterializeSensorFlag} from '../assets/AutoMaterializeSensorFlag';
import {AutomaterializationRoot} from '../assets/auto-materialization/AutomaterializationRoot';
import {InstanceBackfillsRoot} from '../instance/InstanceBackfillsRoot';
import {BackfillPage} from '../instance/backfill/BackfillPage';

export const OverviewRoot = () => {
  const {flagLegacyNav} = useFeatureFlags();
  const automaterializeSensorsFlagState = useAutoMaterializeSensorFlag();
  return (
    <Switch>
      <Route path="/overview/activity" isNestingRoute>
        <OverviewActivityRoot />
      </Route>
      <Route
        path="/overview/jobs"
        render={() => (flagLegacyNav ? <OverviewJobsRoot /> : <Redirect to="/jobs" />)}
      />
      <Route
        path="/overview/schedules"
        render={() => (flagLegacyNav ? <OverviewSchedulesRoot /> : <Redirect to="/automation" />)}
      />
      <Route
        path="/overview/sensors"
        render={() => (flagLegacyNav ? <OverviewSensorsRoot /> : <Redirect to="/automation" />)}
      />
      <Route
        path="/overview/automation"
        render={() =>
          !flagLegacyNav && automaterializeSensorsFlagState !== 'has-global-amp' ? (
            <Redirect to="/automation" />
          ) : (
            <AutomaterializationRoot />
          )
        }
      />
      {featureEnabled(FeatureFlag.flagLegacyRunsPage)
        ? [
            <Route
              path="/overview/backfills/:backfillId"
              render={() => <BackfillPage />}
              key="1"
            />,
            <Route
              path="/overview/backfills"
              exact
              render={() => <InstanceBackfillsRoot />}
              key="2"
            />,
          ]
        : null}
      <Route path="/overview/resources">
        <OverviewResourcesRoot />
      </Route>
      <Route path="*" isNestingRoute render={() => <Redirect to="/overview/activity" />} />
    </Switch>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default OverviewRoot;
