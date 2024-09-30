import {Redirect, Switch} from 'react-router-dom';

import {OverviewActivityRoot} from './OverviewActivityRoot';
import {OverviewJobsRoot} from './OverviewJobsRoot';
import {OverviewResourcesRoot} from './OverviewResourcesRoot';
import {OverviewSchedulesRoot} from './OverviewSchedulesRoot';
import {OverviewSensorsRoot} from './OverviewSensorsRoot';
import {FeatureFlag} from '../../../../../../../internal/dagster-cloud/js_modules/app-cloud/src/settings/FeatureFlags.cloud';
import {featureEnabled, useFeatureFlags} from '../app/Flags';
import {Route} from '../app/Route';
import {useAutoMaterializeSensorFlag} from '../assets/AutoMaterializeSensorFlag';
import {AutomaterializationRoot} from '../assets/auto-materialization/AutomaterializationRoot';
import {InstanceBackfillsRoot} from '../instance/InstanceBackfillsRoot';
import {BackfillPage} from '../instance/backfill/BackfillPage';

export const OverviewRoot = () => {
  const {flagSettingsPage} = useFeatureFlags();
  const automaterializeSensorsFlagState = useAutoMaterializeSensorFlag();
  return (
    <Switch>
      <Route path="/overview/activity" isNestingRoute>
        <OverviewActivityRoot />
      </Route>
      <Route
        path="/overview/jobs"
        render={() => (flagSettingsPage ? <Redirect to="/jobs" /> : <OverviewJobsRoot />)}
      />
      <Route
        path="/overview/schedules"
        render={() =>
          flagSettingsPage ? <Redirect to="/automation" /> : <OverviewSchedulesRoot />
        }
      />
      <Route
        path="/overview/sensors"
        render={() => (flagSettingsPage ? <Redirect to="/automation" /> : <OverviewSensorsRoot />)}
      />
      <Route
        path="/overview/automation"
        render={() =>
          flagSettingsPage && automaterializeSensorsFlagState !== 'has-global-amp' ? (
            <Redirect to="/automation" />
          ) : (
            <AutomaterializationRoot />
          )
        }
      />
      {featureEnabled(FeatureFlag.flagRunsFeed) ? (
        <Route path="/overview/backfills/:backfillId" render={() => <BackfillPage />} />
      ) : null}
      <Route path="/overview/backfills" exact render={() => <InstanceBackfillsRoot />} />
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
