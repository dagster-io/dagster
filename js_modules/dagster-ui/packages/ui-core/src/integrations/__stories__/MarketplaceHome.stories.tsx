import {Box, Colors} from '@dagster-io/ui-components';
import {Meta} from '@storybook/react';

import {MarketplaceHome} from '../MarketplaceHome';
import * as allIntegrations from '../__generated__';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Integrations/MarketplaceHome',
  component: MarketplaceHome,
} as Meta;

export const Default = () => {
  const integrations = Object.values(allIntegrations);
  return (
    <Box padding={64} style={{width: '1300px', backgroundColor: Colors.backgroundLight()}}>
      <MarketplaceHome integrations={integrations} />
    </Box>
  );
};
