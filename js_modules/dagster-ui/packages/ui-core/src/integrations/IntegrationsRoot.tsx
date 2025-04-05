import {Route, Switch} from 'react-router';

import {IntegrationRoot} from './IntegrationRoot';
import {MarketplaceRoot} from './MarketplaceRoot';

export const IntegrationsRoot = () => {
  return (
    <Switch>
      <Route path="/integrations" component={MarketplaceRoot} exact />
      <Route path="/integrations/:integrationName" component={IntegrationRoot} />
    </Switch>
  );
};
