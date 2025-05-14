import {Box, Colors} from '@dagster-io/ui-components';
import {Meta} from '@storybook/react';

import {MarketplaceHome} from '../MarketplaceHome';
import {IntegrationFrontmatter} from '../types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Integrations/MarketplaceHome',
  component: MarketplaceHome,
} as Meta;

export const Default = () => {
  const integrations: IntegrationFrontmatter[] = [
    {
      id: 'airlift',
      title: 'Dagster & Airlift',
      name: 'Airlift',
      description: 'Easily integrate Dagster and Airflow.',
      tags: ['dagster-supported', 'other'],
      source:
        'https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-airlift',
      pypi: 'https://pypi.org/project/dagster-airlift/',
      partnerlink: '',
      logoFilename: 'airflow.svg',
    },
    {
      id: 'anthropic',
      title: 'Dagster & Anthropic',
      name: 'Anthropic',
      description:
        'Integrate Anthropic calls into your Dagster pipelines, without breaking the bank.',
      tags: ['community-supported'],
      source:
        'https://github.com/dagster-io/community-integrations/tree/main/libraries/dagster-anthropic',
      pypi: 'https://pypi.org/project/dagster-anthropic/',
      partnerlink: '',
      logoFilename: 'anthropic.svg',
    },
    {
      id: 'azure-adls2',
      title: 'Dagster &  Azure Data Lake Storage Gen 2',
      name: 'Azure Data Lake Storage Gen 2',
      description: 'Get utilities for ADLS2 and Blob Storage.',
      tags: ['dagster-supported', 'storage'],
      source:
        'https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-azure',
      pypi: 'https://pypi.org/project/dagster-azure/',
      partnerlink: '',
      logoFilename: 'azure.svg',
    },
  ];

  return (
    <Box padding={64} style={{width: '1300px', backgroundColor: Colors.backgroundLight()}}>
      <MarketplaceHome integrations={integrations} />
    </Box>
  );
};
