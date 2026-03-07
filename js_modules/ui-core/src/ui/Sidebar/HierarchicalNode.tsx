import {Box, Icon} from '@dagster-io/ui-components';
import * as React from 'react';

import {FocusableLabelContainer} from './FocusableLabelContainer';
import styles from './HierarchicalNode.module.css';
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
    onSelect: (e: React.MouseEvent<any> | React.KeyboardEvent<any>) => void;
    onToggleOpen?: () => void;
  }) => {
    const paddingLeft = node.level * 16;

    return (
      <Box style={{paddingLeft}} flex={{alignItems: 'center'}}>
        {node.type === 'folder' && node.hasChildren && onToggleOpen && (
          <SidebarDisclosureTriangle isOpen={isOpen} toggleOpen={onToggleOpen} />
        )}
        <div className={styles.itemContainer} onClick={onSelect}>
          {node.type === 'folder' && !node.hasChildren && (
            <div style={{width: 18, flexShrink: 0}} />
          )}
          {node.type === 'file' && <div style={{width: 20, flexShrink: 0}} />}

          <FocusableLabelContainer
            isSelected={isSelected}
            isLastSelected={isLastSelected}
            icon={<Icon name={node.icon} />}
            text={node.name}
          />
        </div>
      </Box>
    );
  },
);
