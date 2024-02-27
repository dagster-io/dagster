import {
  Box,
  Colors,
  Icon,
  MiddleTruncate,
  Popover,
  UnstyledButton,
} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {StatusDot} from './StatusDot';
import {FolderNodeNonAssetType, getDisplayName} from './util';
import {ExplorerPath} from '../../pipelines/PipelinePathUtils';
import {AssetGroup} from '../AssetGraphExplorer';
import {AssetNodeMenuProps, useAssetNodeMenu} from '../AssetNodeMenu';
import {useGroupNodeContextMenu} from '../CollapsedGroupNode';
import {GraphData, GraphNode} from '../Utils';

export const AssetSidebarNode = ({
  node,
  level,
  toggleOpen,
  selectNode,
  isOpen,
  isSelected,
  selectThisNode,
  explorerPath,
  onChangeExplorerPath,
  fullAssetGraphData,
  isLastSelected,
  onFilterToGroup,
}: {
  fullAssetGraphData: GraphData;
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
}) => {
  const isGroupNode = 'groupNode' in node;
  const isLocationNode = 'locationName' in node;
  const isAssetNode = !isGroupNode && !isLocationNode;

  const displayName = React.useMemo(() => {
    if (isAssetNode) {
      return getDisplayName(node);
    } else if (isGroupNode) {
      return node.groupNode.groupName;
    } else {
      return node.locationName;
    }
  }, [isAssetNode, isGroupNode, node]);

  const elementRef = React.useRef<HTMLDivElement | null>(null);

  const showArrow = !isAssetNode;

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
    <>
      <Box ref={elementRef} padding={{left: 8}}>
        <BoxWrapper level={level}>
          <ItemContainer
            padding={{right: 12}}
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
            <GrayOnHoverBox
              style={{
                width: '100%',
                borderRadius: '8px',
                ...(isSelected ? {background: Colors.backgroundBlue()} : {}),
              }}
              ref={ref}
            >
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'auto minmax(0, 1fr)',
                  gap: '6px',
                  alignItems: 'center',
                }}
              >
                {isAssetNode ? (
                  <StatusDot node={node} />
                ) : isGroupNode ? (
                  <Icon name="asset_group" />
                ) : isLocationNode ? (
                  <Icon name="folder_open" />
                ) : null}
                <MiddleTruncate text={displayName} />
              </div>
            </GrayOnHoverBox>
            {isAssetNode ? (
              <ExpandMore>
                <AssetNodePopoverMenu
                  graphData={fullAssetGraphData}
                  node={node}
                  selectNode={selectNode}
                  explorerPath={explorerPath}
                  onChangeExplorerPath={onChangeExplorerPath}
                />
              </ExpandMore>
            ) : isGroupNode ? (
              <ExpandMore>
                <AssetGroupPopoverMenu
                  onFilterToGroup={() => onFilterToGroup(node.groupNode)}
                  assets={node.groupNode.assets}
                />
              </ExpandMore>
            ) : null}
          </ItemContainer>
        </BoxWrapper>
      </Box>
    </>
  );
};

const AssetGroupPopoverMenu = (props: Parameters<typeof useGroupNodeContextMenu>[0]) => {
  const {menu, dialog} = useGroupNodeContextMenu(props);
  return (
    <>
      {dialog}
      <Popover
        content={menu}
        placement="right"
        shouldReturnFocusOnClose
        canEscapeKeyClose
        modifiers={{offset: {enabled: true, options: {offset: [0, 12]}}}}
      >
        <UnstyledButton>
          <Icon name="more_horiz" color={Colors.accentGray()} />
        </UnstyledButton>
      </Popover>
    </>
  );
};

const AssetNodePopoverMenu = (props: AssetNodeMenuProps) => {
  const {menu, dialog} = useAssetNodeMenu(props);
  return (
    <>
      {dialog}
      <Popover
        content={menu}
        placement="right"
        shouldReturnFocusOnClose
        canEscapeKeyClose
        modifiers={{offset: {enabled: true, options: {offset: [0, 12]}}}}
      >
        <UnstyledButton>
          <Icon name="more_horiz" color={Colors.accentGray()} />
        </UnstyledButton>
      </Popover>
    </>
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

const ExpandMore = styled.div`
  position: absolute;
  top: 8px;
  right: 20px;
  visibility: hidden;
`;

const GrayOnHoverBox = styled(UnstyledButton)`
  border-radius: 8px;
  user-select: none;
  width: 100%;
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 5px 8px;
  justify-content: space-between;
  gap: 6;
  flex-grow: 1;
  flex-shrink: 1;
  transition: background 100ms linear;
`;

const ItemContainer = styled(Box)`
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
