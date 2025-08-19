import {Redirect, Switch} from 'react-router-dom';

import {IntegrationListRoot} from './IntegrationListRoot';
import {SingleIntegrationRoot} from './SingleIntegrationRoot';
import {Route} from '../app/Route';
import {useFeatureFlags} from '../app/useFeatureFlags';

const IntegrationsRoot = () => {
  const {flagMarketplace} = useFeatureFlags();

  if (!flagMarketplace) {
    return <Redirect to="/deployment" />;
  }

  return (
    <Switch>
      <Route path="/integrations" component={IntegrationListRoot} exact />
      <Route path="/integrations/:integrationId" component={SingleIntegrationRoot} />
    </Switch>
  );
};

// eslint-disable-next-line import/no-default-export
export default IntegrationsRoot;
