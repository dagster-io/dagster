import {Box, SubwayDot, Tag} from '@dagster-io/ui';
import React from 'react';

type Props = {
  email: string;
  hideIcon?: boolean;
  hideEmail?: boolean;
};
/**
 * This exists mainly for cloud to be able to override this component and show user profiles in dagit.
 * Can be overridden using `LaunchpadHooksContext`
 */
export function UserDisplay({email, hideIcon, hideEmail}: Props) {
  return (
    <Box flex={{direction: 'row', gap: 4}}>
      {hideIcon ? null : <SubwayDot label={email} />}
      {hideEmail ? null : (
        <Tag key="user" icon="account_circle">
          {email}
        </Tag>
      )}
    </Box>
  );
}
