import {Redirect, Route, Switch} from 'react-router';

import {MarketplaceRoot} from './MarketplaceRoot';
import {SingleIntegrationRoot} from './SingleIntegrationRoot';
import {useFeatureFlags} from '../app/Flags';

const IntegrationsRoot = () => {
  const {flagMarketplace} = useFeatureFlags();

  if (!flagMarketplace) {
    return <Redirect to="/deployment" />;
  }

  return (
    <Switch>
      <Route path="/integrations" component={MarketplaceRoot} exact />
      <Route path="/integrations/:integrationName" component={SingleIntegrationRoot} />
    </Switch>
  );
};

// eslint-disable-next-line import/no-default-export
export default IntegrationsRoot;
