import {Box} from '@dagster-io/ui-components';
import {Redirect, Switch} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {Route} from '../app/Route';
import {CodeLocationsPageContent} from '../instance/CodeLocationsPage';
import {InstanceConcurrencyPageContent} from '../instance/InstanceConcurrency';
import {InstanceConfigContent} from '../instance/InstanceConfig';
import {InstanceHealthPageContent} from '../instance/InstanceHealthPage';

export const SettingsMainPane = () => {
  const {flagLegacyNav} = useFeatureFlags();
  if (flagLegacyNav) {
    return <Redirect to="/locations" />;
  }

  return (
    <Box flex={{direction: 'column', alignItems: 'stretch'}} style={{flex: 1, overflow: 'hidden'}}>
      <Switch>
        <Route path="/deployment/locations">
          <CodeLocationsPageContent />
        </Route>
        <Route path="/deployment/daemons">
          <InstanceHealthPageContent />
        </Route>
        <Route path="/deployment/concurrency">
          <InstanceConcurrencyPageContent />
        </Route>
        <Route path="/deployment/config">
          <InstanceConfigContent />
        </Route>
        <Route path="*" isNestingRoute>
          <Redirect to="/deployment/locations" />
        </Route>
      </Switch>
    </Box>
  );
};
