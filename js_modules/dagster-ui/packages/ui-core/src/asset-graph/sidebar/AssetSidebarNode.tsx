import {Box, Colors, Icon, MiddleTruncate, UnstyledButton} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {StatusDot, StatusDotNode} from './StatusDot';
import {
  FolderNodeCodeLocationType,
  FolderNodeGroupType,
  FolderNodeNonAssetType,
  getDisplayName,
} from './util';
import {ExplorerPath} from '../../pipelines/PipelinePathUtils';
import {AssetGroup} from '../AssetGraphExplorer';
import {AssetNodeMenuProps, useAssetNodeMenu} from '../AssetNodeMenu';
import {useGroupNodeContextMenu} from '../CollapsedGroupNode';
import {ContextMenuWrapper, triggerContextMenu} from '../ContextMenuWrapper';
import {GraphData, GraphNode} from '../Utils';

type AssetSidebarNodeProps = {
  fullAssetGraphData?: GraphData;
  node: GraphNode | FolderNodeNonAssetType;
  level: number;
  toggleOpen: () => void;
  selectThisNode: (e: React.MouseEvent<any> | React.KeyboardEvent<any>) => void;
  selectNode: (e: React.MouseEvent<any> | React.KeyboardEvent<any>, nodeId: string) => void;
  isOpen: boolean;
  isLastSelected: boolean;
  isSelected: boolean;
  explorerPath: ExplorerPath;
  onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
  onFilterToGroup: (group: AssetGroup) => void;
};

export const AssetSidebarNode = (props: AssetSidebarNodeProps) => {
  const {node, level, toggleOpen, isOpen, selectThisNode} = props;
  const isGroupNode = 'groupNode' in node;
  const isLocationNode = 'locationName' in node;
  const isAssetNode = !isGroupNode && !isLocationNode;

  const elementRef = React.useRef<HTMLDivElement | null>(null);

  const showArrow = !isAssetNode;

  return (
    <Box ref={elementRef} padding={{left: 8, right: 12}}>
      <BoxWrapper level={level}>
        <ItemContainer
          flex={{direction: 'row', alignItems: 'center'}}
          onClick={selectThisNode}
          onDoubleClick={(e) => !e.metaKey && toggleOpen()}
        >
          {showArrow ? (
            <UnstyledButton
              onClick={(e) => {
                e.stopPropagation();
                toggleOpen();
              }}
              onDoubleClick={(e) => {
                e.stopPropagation();
              }}
              onKeyDown={(e) => {
                if (e.code === 'Space') {
                  // Prevent the default scrolling behavior
                  e.preventDefault();
                }
              }}
              style={{cursor: 'pointer', width: 18}}
            >
              <Icon
                name="arrow_drop_down"
                style={{transform: isOpen ? 'rotate(0deg)' : 'rotate(-90deg)'}}
              />
            </UnstyledButton>
          ) : level === 1 && isAssetNode ? (
            // Special case for when asset nodes are at the root (level = 1) due to their being only a single group.
            // In this case we don't need the spacer div to align nodes because  none of the nodes will be collapsible/un-collapsible.
            <div />
          ) : (
            // Spacer div to align nodes with collapse/un-collapse arrows with nodes that don't have collapse/un-collapse arrows
            <div style={{width: 18}} />
          )}
          {isAssetNode ? (
            <AssetSidebarAssetLabel {...props} node={node} />
          ) : isGroupNode ? (
            <AssetSidebarGroupLabel {...props} node={node} />
          ) : (
            <AssetSidebarLocationLabel {...props} node={node} />
          )}
        </ItemContainer>
      </BoxWrapper>
    </Box>
  );
};

type AssetSidebarAssetLabelProps = {
  fullAssetGraphData?: GraphData;
  node: AssetNodeMenuProps['node'] & StatusDotNode;
  selectNode: (e: React.MouseEvent<any> | React.KeyboardEvent<any>, nodeId: string) => void;
  isLastSelected: boolean;
  isSelected: boolean;
  explorerPath: ExplorerPath;
  onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
};

const AssetSidebarAssetLabel = ({
  node,
  isSelected,
  isLastSelected,
  fullAssetGraphData,
  selectNode,
  explorerPath,
  onChangeExplorerPath,
}: AssetSidebarAssetLabelProps) => {
  const {menu, dialog} = useAssetNodeMenu({
    graphData: fullAssetGraphData,
    node,
    selectNode,
    explorerPath,
    onChangeExplorerPath,
  });

  return (
    <ContextMenuWrapper stopPropagation menu={menu} wrapperOuterStyles={{width: '100%'}}>
      <FocusableLabelContainer
        isSelected={isSelected}
        isLastSelected={isLastSelected}
        icon={<StatusDot node={node} />}
        text={getDisplayName(node)}
      />
      <ExpandMore onClick={triggerContextMenu}>
        <Icon name="more_horiz" color={Colors.accentGray()} />
      </ExpandMore>
      {dialog}
    </ContextMenuWrapper>
  );
};

const AssetSidebarGroupLabel = ({
  node,
  isSelected,
  isLastSelected,
  onFilterToGroup,
}: Omit<AssetSidebarNodeProps, 'node'> & {node: FolderNodeGroupType}) => {
  const {menu, dialog} = useGroupNodeContextMenu({
    onFilterToGroup: () => onFilterToGroup(node.groupNode),
    assets: node.groupNode.assets,
  });

  return (
    <ContextMenuWrapper stopPropagation menu={menu} wrapperOuterStyles={{width: '100%'}}>
      <FocusableLabelContainer
        isSelected={isSelected}
        isLastSelected={isLastSelected}
        icon={<Icon name="asset_group" />}
        text={node.groupNode.groupName}
      />
      <ExpandMore onClick={triggerContextMenu}>
        <Icon name="more_horiz" color={Colors.accentGray()} />
      </ExpandMore>
      {dialog}
    </ContextMenuWrapper>
  );
};

const AssetSidebarLocationLabel = ({
  node,
  isSelected,
  isLastSelected,
}: Omit<AssetSidebarNodeProps, 'node'> & {node: FolderNodeCodeLocationType}) => {
  return (
    <Box style={{width: '100%'}} onContextMenu={(e) => e.preventDefault()}>
      <FocusableLabelContainer
        isSelected={isSelected}
        isLastSelected={isLastSelected}
        icon={<Icon name="folder_open" />}
        text={node.locationName}
      />
    </Box>
  );
};

const FocusableLabelContainer = ({
  isSelected,
  isLastSelected,
  icon,
  text,
}: {
  isSelected: boolean;
  isLastSelected: boolean;
  icon: React.ReactNode;
  text: string;
}) => {
  const ref = React.useRef<HTMLButtonElement | null>(null);
  React.useLayoutEffect(() => {
    // When we click on a node in the graph it also changes "isSelected" in the sidebar.
    // We want to check if the focus is currently in the graph and if it is lets keep it there
    // Otherwise it means the click happened in the sidebar in which case we should move focus to the element
    // in the sidebar
    if (ref.current && isLastSelected && !isElementInsideSVGViewport(document.activeElement)) {
      ref.current.focus();
    }
  }, [isLastSelected]);

  return (
    <GrayOnHoverBox
      ref={ref}
      style={{
        gridTemplateColumns: icon ? 'auto minmax(0, 1fr)' : 'minmax(0, 1fr)',
        ...(isSelected ? {background: Colors.backgroundBlue()} : {}),
      }}
    >
      {icon}
      <MiddleTruncate text={text} />
    </GrayOnHoverBox>
  );
};

const BoxWrapper = ({level, children}: {level: number; children: React.ReactNode}) => {
  const wrapper = React.useMemo(() => {
    let sofar = children;
    for (let i = 0; i < level; i++) {
      sofar = (
        <Box
          padding={{left: 8}}
          margin={{left: 8}}
          border={
            i < level - 1 ? {side: 'left', width: 1, color: Colors.keylineDefault()} : undefined
          }
          style={{position: 'relative'}}
        >
          {sofar}
        </Box>
      );
    }
    return sofar;
  }, [level, children]);

  return <>{wrapper}</>;
};

const ExpandMore = styled(UnstyledButton)`
  position: absolute;
  top: 8px;
  right: 8px;
  visibility: hidden;
`;

const GrayOnHoverBox = styled(UnstyledButton)`
  border-radius: 8px;
  user-select: none;
  width: 100%;
  display: grid;
  flex-direction: row;
  height: 32px;
  align-items: center;
  padding: 5px 8px;
  justify-content: space-between;
  gap: 6px;
  flex-grow: 1;
  flex-shrink: 1;
  transition: background 100ms linear;
`;

export const ItemContainer = styled(Box)`
  height: 32px;
  position: relative;
  cursor: pointer;

  &:hover,
  &:focus-within {
    ${GrayOnHoverBox} {
      background: ${Colors.backgroundLightHover()};
    }

    ${ExpandMore} {
      visibility: visible;
    }
  }
`;

function isElementInsideSVGViewport(element: Element | null) {
  return !!element?.closest('[data-svg-viewport]');
}
