import React from 'react';

import {BaseTag, Box, SubwayDot} from '@dagster-io/ui-components';

type Props = {
  email: string;
  isFilter?: boolean;
};
/**
 * This exists mainly for cloud to be able to override this component and show user profiles in the Dagster UI..
 * Can be overridden using `LaunchpadHooksContext`
 * This is primarily used to display users in filter dropdown + users in table cells
 */
export function UserDisplay({email, isFilter}: Props) {
  const icon = <SubwayDot label={email} blobSize={16} fontSize={10} />;
  return isFilter ? (
    <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
      <span>{icon}</span>
      {email}
    </Box>
  ) : (
    <BaseTag key="user" icon={<div style={{margin: '0 4px 0 -4px'}}>{icon}</div>} label={email} />
  );
}
