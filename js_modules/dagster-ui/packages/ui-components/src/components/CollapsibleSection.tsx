import React from 'react';

import {Box} from './Box';
import {Icon} from './Icon';

export const CollapsibleSection = ({
  header,
  headerWrapperProps,
  children,
  isInitiallyCollapsed = false,
}: {
  header: React.ReactNode;
  headerWrapperProps?: React.ComponentProps<typeof Box>;
  children: React.ReactNode;
  isInitiallyCollapsed?: boolean;
}) => {
  const [isCollapsed, setIsCollapsed] = React.useState(isInitiallyCollapsed);
  return (
    <Box flex={{direction: 'column'}}>
      <Box
        {...headerWrapperProps}
        flex={{direction: 'row', alignItems: 'center', gap: 6, ...(headerWrapperProps?.flex || {})}}
        onClick={() => {
          setIsCollapsed(!isCollapsed);
          headerWrapperProps?.onClick?.();
        }}
      >
        <Icon
          name="arrow_drop_down"
          style={{transform: isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)'}}
        />
        <div>{header}</div>
      </Box>
      {isCollapsed ? null : children}
    </Box>
  );
};
