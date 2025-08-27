import {useIntegrationsProvider} from 'shared/integrations/useIntegrationsProvider.oss';

import {IntegrationListPage} from './IntegrationListPage';
import {useTrackPageView} from '../app/analytics';

export const IntegrationListRoot = () => {
  useTrackPageView();
  const provider = useIntegrationsProvider();

  return <IntegrationListPage provider={provider} />;
};
