import {Box} from '@dagster-io/ui-components';
import {Redirect, Route, Switch} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {CodeLocationsPageContent} from '../instance/CodeLocationsPage';
import {InstanceConcurrencyPageContent} from '../instance/InstanceConcurrency';
import {InstanceConfigContent} from '../instance/InstanceConfig';
import {InstanceHealthPageContent} from '../instance/InstanceHealthPage';

export const SettingsMainPane = () => {
  const {flagSettingsPage} = useFeatureFlags();
  if (!flagSettingsPage) {
    return <Redirect to="/locations" />;
  }

  return (
    <Box flex={{direction: 'column', alignItems: 'stretch'}} style={{flex: 1, overflow: 'hidden'}}>
      <Switch>
        <Route path="/settings/locations">
          <CodeLocationsPageContent />
        </Route>
        <Route path="/settings/daemons">
          <InstanceHealthPageContent />
        </Route>
        <Route path="/settings/concurrency">
          <InstanceConcurrencyPageContent />
        </Route>
        <Route path="/settings/config">
          <InstanceConfigContent />
        </Route>
        <Route path="*">
          <Redirect to="/settings/locations" />
        </Route>
      </Switch>
    </Box>
  );
};
