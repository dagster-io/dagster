import {Box, Menu, MenuItem} from '@dagster-io/ui-components';
import * as React from 'react';

import {ContextMenuWrapper} from './ContextMenuWrapper';
import {KeyboardTag} from './KeyboardTag';

export const AssetGraphBackgroundContextMenu = ({
  direction,
  setDirection,
  allGroups,
  expandedGroups,
  setExpandedGroups,
  children,
}: {
  direction: 'vertical' | 'horizontal';
  setDirection: (dir: 'vertical' | 'horizontal') => void;
  children: React.ReactNode;

  allGroups?: string[];
  expandedGroups?: string[];
  setExpandedGroups?: (groups: string[]) => void;
}) => {
  const areAllGroupsCollapsed = !expandedGroups || expandedGroups.length === 0;
  const areAllGroupsExpanded =
    !expandedGroups ||
    !allGroups ||
    allGroups.length === 1 ||
    expandedGroups.length === allGroups.length;

  return (
    <ContextMenuWrapper
      wrapperOuterStyles={{width: '100%', height: '100%'}}
      wrapperInnerStyles={{width: '100%', height: '100%'}}
      menu={
        <Menu>
          {areAllGroupsCollapsed ? null : (
            <MenuItem
              text={
                <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                  Collapse all groups <KeyboardTag>⌥E</KeyboardTag>
                </Box>
              }
              icon="unfold_less"
              onClick={() => {
                setExpandedGroups?.([]);
              }}
            />
          )}
          {areAllGroupsExpanded ? null : (
            <MenuItem
              text={
                <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                  Expand all groups
                  {areAllGroupsCollapsed ? <KeyboardTag>⌥E</KeyboardTag> : null}
                </Box>
              }
              icon="unfold_more"
              onClick={() => {
                setExpandedGroups?.(allGroups!);
              }}
            />
          )}
          {direction === 'horizontal' ? (
            <MenuItem
              text={
                <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                  Set vertical orientation <KeyboardTag>⌥O</KeyboardTag>
                </Box>
              }
              icon="graph_vertical"
              onClick={() => setDirection?.('vertical')}
            />
          ) : (
            <MenuItem
              text={
                <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                  Set horizontal orientation <KeyboardTag>⌥O</KeyboardTag>
                </Box>
              }
              icon="graph_horizontal"
              onClick={() => setDirection?.('horizontal')}
            />
          )}
        </Menu>
      }
    >
      {children}
    </ContextMenuWrapper>
  );
};
