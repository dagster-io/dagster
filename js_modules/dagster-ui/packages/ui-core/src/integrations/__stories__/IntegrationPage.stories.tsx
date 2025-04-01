import {Box, Colors} from '@dagster-io/ui-components';
import {Meta} from '@storybook/react';

import {IntegrationPage} from '../IntegrationPage';
import {IntegrationTag} from '../IntegrationTag';
import {IntegrationDetails} from '../types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Integrations/IntegrationPage',
  component: IntegrationPage,
} as Meta;

const MARKDOWN = `
Using this integration, you can trigger Airbyte syncs and orchestrate your Airbyte connections from within Dagster, making it easy to chain an Airbyte sync with upstream or downstream steps in your workflow.

### Installation

\`\`\`bash
pip install dagster-airbyte
\`\`\`

### Example

\`\`\`python
from dagster import EnvVar
from dagster_airbyte import AirbyteResource, load_assets_from_airbyte_instance
import os

# Connect to your OSS Airbyte instance
airbyte_instance = AirbyteResource(
    host="localhost",
    port="8000",
    # If using basic auth, include username and password:
    username="airbyte",
    password=EnvVar("AIRBYTE_PASSWORD")
)

# Load all assets from your Airbyte instance
airbyte_assets = load_assets_from_airbyte_instance(airbyte_instance)
\`\`\`

### About Airbyte

**Airbyte** is an open source data integration engine that helps you consolidate your SaaS application and database data into your data warehouses, lakes and databases.
`;

export const Default = () => {
  const integration: IntegrationDetails = {
    id: 'airbyte',
    name: 'Airbyte',
    logo: 'airbyte',
    tags: [IntegrationTag.EltTools],
    status: 'published',
    title: 'Airbyte',
    excerpt: 'Airbyte is a tool for syncing data between databases.',
    date: '2025-03-14',
    apireflink: 'https://docs.airbyte.com/api',
    docslink: 'https://docs.airbyte.com',
    partnerlink: 'https://airbyte.com',
    categories: ['data-integration'],
    enabledBy: ['dagster'],
    markdown: MARKDOWN,
  };

  return (
    <Box
      style={{
        width: '1300px',
        height: '100%',
        overflowY: 'auto',
        backgroundColor: Colors.backgroundLight(),
      }}
    >
      <IntegrationPage integration={integration} />
    </Box>
  );
};
