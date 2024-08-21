import {Box, Colors, Subheading} from '@dagster-io/ui-components';
import {ComponentProps, ReactNode} from 'react';

export const CodeLocationOverviewSectionHeader = ({
  label,
  border = null,
}: {
  label: ReactNode;
  border?: ComponentProps<typeof Box>['border'];
}) => (
  <Box
    background={Colors.backgroundLight()}
    border={border}
    padding={{horizontal: 24, vertical: 8}}
  >
    <Subheading>{label}</Subheading>
  </Box>
);
