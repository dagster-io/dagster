import {Redirect, Switch} from 'react-router-dom';

import {OverviewActivityRoot} from './OverviewActivityRoot';
import {OverviewJobsRoot} from './OverviewJobsRoot';
import {OverviewResourcesRoot} from './OverviewResourcesRoot';
import {OverviewSchedulesRoot} from './OverviewSchedulesRoot';
import {OverviewSensorsRoot} from './OverviewSensorsRoot';
import {useFeatureFlags} from '../app/Flags';
import {Route} from '../app/Route';
import {AutomaterializationRoot} from '../assets/auto-materialization/AutomaterializationRoot';
import {InstanceBackfillsRoot} from '../instance/InstanceBackfillsRoot';
import {BackfillPage} from '../instance/backfill/BackfillPage';

export const OverviewRoot = () => {
  const {flagSettingsPage} = useFeatureFlags();
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
          flagSettingsPage ? <Redirect to="/automation/schedules" /> : <OverviewSchedulesRoot />
        }
      />
      <Route
        path="/overview/sensors"
        render={() =>
          flagSettingsPage ? <Redirect to="/automation/sensors" /> : <OverviewSensorsRoot />
        }
      />
      <Route
        path="/overview/automation"
        render={() =>
          flagSettingsPage ? <Redirect to="/automation" /> : <AutomaterializationRoot />
        }
      />
      <Route
        path="/overview/backfills/:backfillId"
        render={({match}) =>
          flagSettingsPage ? (
            <Redirect to={`/automation/backfills/${match.params.backfillId}`} />
          ) : (
            <BackfillPage />
          )
        }
      />
      <Route
        path="/overview/backfills"
        exact
        render={() =>
          flagSettingsPage ? <Redirect to="/automation/backfills" /> : <InstanceBackfillsRoot />
        }
      />
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
