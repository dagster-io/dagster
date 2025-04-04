import {Box, Colors} from '@dagster-io/ui-components';
import {Meta} from '@storybook/react';

import {MarketplaceHome} from '../MarketplaceHome';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Integrations/MarketplaceHome',
  component: MarketplaceHome,
} as Meta;

export const Default = () => {
  const integrations = [
    {
      id: 'dbt',
      status: 'published',
      name: 'dbt',
      title: 'Dagster & dbt',
      excerpt: '',
      partnerlink: '',
      categories: [],
      enabledBy: [],
      enables: [],
      tags: [],
      logoFilename: 'dbt.svg',
      pypiUrl: '',
      repoUrl: '',
    },
  ];

  return (
    <Box padding={64} style={{width: '1300px', backgroundColor: Colors.backgroundLight()}}>
      <MarketplaceHome integrations={integrations} />
    </Box>
  );
};
