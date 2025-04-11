import {Box, Icon} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import styles from './css/MarketplaceTopNavLink.module.css';

export const MarketplaceTopNavLink = () => {
  return (
    <Link className={styles.marketplaceTopNavLink} to="/integrations">
      <Box
        flex={{direction: 'row', alignItems: 'center', gap: 8, justifyContent: 'center'}}
        className={styles.marketplaceTopNavLinkContent}
      >
        <Icon name="compute_kind" />
        Integrations
      </Box>
    </Link>
  );
};
