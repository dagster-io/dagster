import {Box, Colors} from '@dagster-io/ui-components';
import {Meta} from '@storybook/react';

import {IntegrationPage} from '../IntegrationPage';
import {airbyte} from '../__generated__';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Integrations/IntegrationPage',
  component: IntegrationPage,
} as Meta;

export const Default = () => {
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
