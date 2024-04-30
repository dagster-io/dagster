// eslint-disable-next-line no-restricted-imports
import {Collapse} from '@blueprintjs/core';
import {Box, Icon, IconName, Subtitle1, UnstyledButton} from '@dagster-io/ui-components';
import React from 'react';

import {useStateWithStorage} from '../hooks/useStateWithStorage';

export const LargeCollapsibleSection = ({
  header,
  count,
  icon,
  children,
  right,
  collapsedByDefault = false,
  padHeader = false,
  padChildren = true,
}: {
  header: string;
  count?: number;
  icon?: IconName;
  children: React.ReactNode;
  right?: React.ReactNode;
  collapsedByDefault?: boolean;
  padHeader?: boolean;
  padChildren?: boolean;
}) => {
  const [isCollapsed, setIsCollapsed] = useStateWithStorage<boolean>(
    `collapsible-section-${header}`,
    (storedValue) =>
      storedValue === true || storedValue === false ? storedValue : collapsedByDefault,
  );

  return (
    <Box flex={{direction: 'column'}}>
      <UnstyledButton onClick={() => setIsCollapsed(!isCollapsed)}>
        <Box
          flex={{direction: 'row', alignItems: 'center', gap: 6}}
          padding={{vertical: 12, right: 12, left: padHeader ? 24 : 0}}
          border="bottom"
        >
          {icon && <Icon size={20} name={icon} />}
          <Subtitle1 style={{flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis'}}>
            {header}
            {count !== undefined ? ` (${count.toLocaleString()})` : ''}
          </Subtitle1>
          {right}
          <Icon
            name="arrow_drop_down"
            size={20}
            style={{transform: isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)'}}
          />
        </Box>
      </UnstyledButton>
      <Collapse isOpen={!isCollapsed}>
        <Box padding={{vertical: padChildren ? 12 : 0}}>{children}</Box>
      </Collapse>
    </Box>
  );
};
