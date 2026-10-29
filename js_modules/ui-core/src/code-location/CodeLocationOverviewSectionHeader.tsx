import {Box, Colors, Heading} from '@dagster-io/ui-components';
import {ComponentProps, ReactNode} from 'react';

import styles from './css/CodeLocationOverviewSectionHeader.module.css';

export const CodeLocationOverviewSectionHeader = ({
  label,
  border = null,
}: {
  label: ReactNode;
  border?: ComponentProps<typeof Box>['border'];
}) => (
  <Box background={Colors.backgroundLight()} border={border} className={styles.header}>
    <Heading size={14} weight={600}>
      {label}
    </Heading>
  </Box>
);
