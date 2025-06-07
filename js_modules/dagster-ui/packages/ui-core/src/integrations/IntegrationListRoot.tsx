import {useIntegrationsProvider} from 'shared/integrations/useIntegrationsProvider.oss';

import {IntegrationListPage} from './IntegrationListPage';

export const IntegrationListRoot = () => {
  const provider = useIntegrationsProvider();

  return <IntegrationListPage provider={provider} />;
};
