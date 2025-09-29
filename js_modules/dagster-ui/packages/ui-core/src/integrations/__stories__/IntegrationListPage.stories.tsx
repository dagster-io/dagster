import {Box, Colors} from '@dagster-io/ui-components';
import {useIntegrationsProvider} from 'shared/integrations/useIntegrationsProvider.oss';

import {IntegrationListPage} from '../IntegrationListPage';
import {IntegrationFrontmatter} from '../types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Integrations/IntegrationListPage',
  component: IntegrationListPage,
};

export const Default = () => {
  const provider = useIntegrationsProvider();

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
      logo: null,
      installationCommand: null,
      isPrivate: false,
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
      logo: null,
      installationCommand: null,
      isPrivate: false,
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
      logo: null,
      installationCommand: null,
      isPrivate: false,
    },
    {
      id: 'trino',
      name: 'Trino',
      title: '',
      description:
        'This repository contains an integration between Dagster and Trino that enables users to run Trino queries as part of their Dagster pipelines.',
      logo: '🚜',
      logoFilename: null,
      installationCommand:
        'https://github.com/andreapiso/dagster-trino/archive/refs/heads/main.zip && pip install -e .',
      pypi: null,
      partnerlink: '',
      isPrivate: true,
      source: 'https://github.com/andreapiso/dagster-trino/',
      tags: ['etl', 'compute', 'bi'],
    },
  ];

  return (
    <Box padding={64} style={{width: '1300px', backgroundColor: Colors.backgroundLight()}}>
      <IntegrationListPage provider={{...provider, integrations}} />
    </Box>
  );
};
