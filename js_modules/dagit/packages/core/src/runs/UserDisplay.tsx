import {BaseTag, Box, SubwayDot} from '@dagster-io/ui';
import React from 'react';

type Props = {
  email: string;
  isFilter?: boolean;
};
/**
 * This exists mainly for cloud to be able to override this component and show user profiles in dagit.
 * Can be overridden using `LaunchpadHooksContext`
 * This is primarily used to display users in filter dropdown + users in table cells
 */
export function UserDisplay({email, isFilter}: Props) {
  const icon = <SubwayDot label={email} blobSize={14} fontSize={9} />;
  return isFilter ? (
    <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
      <span>{icon}</span>
      {email}
    </Box>
  ) : (
    <BaseTag key="user" icon={<div style={{marginRight: '4px'}}>{icon}</div>} label={email} />
  );
}
