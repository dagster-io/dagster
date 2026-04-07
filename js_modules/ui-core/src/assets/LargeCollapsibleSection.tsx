import {Box, Icon, IconName, Subtitle1, UnstyledButton} from '@dagster-io/ui-components';
import * as Collapsible from '@radix-ui/react-collapsible';
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
    <Collapsible.Root open={!isCollapsed} onOpenChange={(open) => setIsCollapsed(!open)}>
      <Box flex={{direction: 'column'}}>
        <Collapsible.Trigger asChild>
          <UnstyledButton>
            <Box
              flex={{direction: 'row', alignItems: 'center', gap: 6}}
              padding={{vertical: 12, right: 12, left: padHeader ? 24 : 0}}
              border="bottom"
            >
              {icon && <Icon size={20} name={icon} />}
              <Subtitle1
                style={{flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis'}}
              >
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
        </Collapsible.Trigger>
        <Collapsible.Content style={{overflowX: 'auto'}}>
          <Box padding={{vertical: padChildren ? 12 : 0}}>{children}</Box>
        </Collapsible.Content>
      </Box>
    </Collapsible.Root>
  );
};
