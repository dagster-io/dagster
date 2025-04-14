import {Box, Colors, Page} from '@dagster-io/ui-components';
import {useEffect, useState} from 'react';

import {MarketplaceHome} from './MarketplaceHome';
import {IntegrationFrontmatter} from './types';

const INTEGRATIONS_URL = 'https://integration-registry.dagster.io/api/integrations/index.json';

export const MarketplaceRoot = () => {
  const [integrations, setIntegrations] = useState<IntegrationFrontmatter[]>([]);

  useEffect(() => {
    const fetchIntegrations = async () => {
      const res = await fetch(INTEGRATIONS_URL);
      const data = await res.json();
      setIntegrations(data);
    };
    fetchIntegrations();
  }, []);

  return (
    <Page style={{backgroundColor: Colors.backgroundLight()}}>
      <Box
        padding={{vertical: 32}}
        style={{width: '80vw', maxWidth: '1200px', minWidth: '800px', margin: '0 auto'}}
      >
        <MarketplaceHome integrations={integrations} />
      </Box>
    </Page>
  );
};
