import {Box, Icon} from '@dagster-io/ui-components';
import * as React from 'react';

import {FocusableLabelContainer} from './FocusableLabelContainer';
import {SidebarDisclosureTriangle} from './SidebarDisclosureTriangle';
import {RenderedNode} from './types';

export const HierarchicalNode = React.memo(
  ({
    node,
    isOpen,
    isSelected,
    isLastSelected,
    onToggleOpen,
    onSelect,
  }: {
    node: RenderedNode;
    isOpen: boolean;
    isSelected: boolean;
    isLastSelected: boolean;
    onToggleOpen: () => void;
    onSelect: (e: React.MouseEvent<any> | React.KeyboardEvent<any>) => void;
  }) => {
    const paddingLeft = node.level * 16;

    return (
      <Box flex={{alignItems: 'center'}} style={{paddingLeft}}>
        {node.type === 'folder' && node.hasChildren && (
          <SidebarDisclosureTriangle isOpen={isOpen} toggleOpen={onToggleOpen} />
        )}
        {node.type === 'folder' && !node.hasChildren && (
          <div style={{width: 20, marginRight: 4, flexShrink: 0}} />
        )}
        {node.type === 'file' && <div style={{width: 20, flexShrink: 0}} />}

        <Box style={{width: '100%'}} onClick={onSelect}>
          <FocusableLabelContainer
            isSelected={isSelected}
            isLastSelected={isLastSelected}
            icon={<Icon name={node.icon} />}
            text={node.name}
          />
        </Box>
      </Box>
    );
  },
);
