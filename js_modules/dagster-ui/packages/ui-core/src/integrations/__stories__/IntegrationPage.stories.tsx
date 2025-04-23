import {Box, Colors} from '@dagster-io/ui-components';
import {Meta} from '@storybook/react';

import {IntegrationPage} from '../IntegrationPage';
import {IntegrationFrontmatter} from '../types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Integrations/IntegrationPage',
  component: IntegrationPage,
} as Meta;

export const Default = () => {
  const frontmatter: IntegrationFrontmatter = {
    id: 'airbyte-airbyte-cloud',
    title: 'Using Dagster with Airbyte Cloud',
    name: 'Airbyte Cloud',
    description:
      'Orchestrate Airbyte Cloud connections and schedule syncs alongside upstream or downstream dependencies.',
    tags: ['dagster-supported', 'etl'],
    source:
      'https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-airbyte',
    pypi: 'https://pypi.org/project/dagster-airbyte/',
    partnerlink:
      'https://airbyte.com/tutorials/orchestrate-data-ingestion-and-transformation-pipelines',
    logoFilename: 'airbyte.svg',
  };
  const airbyte = {
    frontmatter,
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
