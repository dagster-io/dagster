import {Box, Colors, Page} from '@dagster-io/ui-components';

import {MarketplaceHome} from './MarketplaceHome';
import * as allIntegrations from './__generated__';

export const MarketplaceRoot = () => {
  const integrations = Object.values(allIntegrations);
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
