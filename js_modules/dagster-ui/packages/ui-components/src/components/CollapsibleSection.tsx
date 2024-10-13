import React from 'react';

import {Box} from './Box';
import {Icon} from './Icon';

export const CollapsibleSection = ({
  header,
  headerWrapperProps,
  children,
  isInitiallyCollapsed = false,
  arrowSide = 'left',
}: {
  header: React.ReactNode;
  headerWrapperProps?: React.ComponentProps<typeof Box>;
  children: React.ReactNode;
  isInitiallyCollapsed?: boolean;
  arrowSide?: 'left' | 'right';
}) => {
  const [isCollapsed, setIsCollapsed] = React.useState(isInitiallyCollapsed);
  return (
    <Box flex={{direction: 'column'}}>
      <Box
        {...headerWrapperProps}
        flex={{
          direction: 'row',
          alignItems: 'center',
          gap: 6,
          grow: 1,
          ...(headerWrapperProps?.flex || {}),
        }}
        onClick={() => {
          setIsCollapsed(!isCollapsed);
          headerWrapperProps?.onClick?.();
        }}
      >
        {arrowSide === 'left' ? (
          <>
            <Icon
              name="arrow_drop_down"
              style={{transform: isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)'}}
            />
            <div style={{userSelect: 'none'}}>{header}</div>
          </>
        ) : (
          <Box style={{flex: 1}} flex={{justifyContent: 'space-between', alignItems: 'center'}}>
            <div style={{userSelect: 'none'}}>{header}</div>
            <Icon
              name="arrow_drop_down"
              style={{transform: isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)'}}
            />
          </Box>
        )}
      </Box>
      {isCollapsed ? null : children}
    </Box>
  );
};
