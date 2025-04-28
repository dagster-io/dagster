import {Box, Colors} from '@dagster-io/ui-components';
import {Meta} from '@storybook/react';

import {IntegrationPage} from '../IntegrationPage';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Integrations/IntegrationPage',
  component: IntegrationPage,
} as Meta;

export const Default = () => {
  const airbyte = {
    frontmatter: {
      id: 'airbyte',
      status: 'published',
      name: 'airbyte',
      title: 'Airbyte',
      excerpt: '',
      partnerlink: '',
      categories: [],
      enabledBy: [],
      enables: [],
      tags: [],
      logoFilename: 'airbyte.svg',
      pypiUrl: '',
      repoUrl: '',
    },
    content: 'placeholder',
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
      <IntegrationPage integration={airbyte} />
    </Box>
  );
};
