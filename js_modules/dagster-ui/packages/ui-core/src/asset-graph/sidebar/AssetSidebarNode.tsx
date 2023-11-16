import {
  Box,
  Icon,
  MiddleTruncate,
  Popover,
  UnstyledButton,
  colorAccentGray,
  colorBackgroundBlue,
  colorBackgroundLight,
  colorKeylineDefault,
} from '@dagster-io/ui-components';
import React from 'react';
import styled from 'styled-components';

import {ExplorerPath} from '../../pipelines/PipelinePathUtils';
import {useAssetNodeMenu} from '../AssetNodeMenu';
import {GraphData, GraphNode} from '../Utils';

import {StatusDot} from './StatusDot';
import {FolderNodeNonAssetType, getDisplayName} from './util';

export const AssetSidebarNode = ({
  graphData,
  node,
  level,
  toggleOpen,
  selectNode,
  isOpen,
  isSelected,
  selectThisNode,
  explorerPath,
  onChangeExplorerPath,
  viewType,
  fullAssetGraphData,
}: {
  graphData: GraphData;
  fullAssetGraphData: GraphData;
  node: GraphNode | FolderNodeNonAssetType;
  level: number;
  toggleOpen: () => void;
  selectThisNode: (e: React.MouseEvent<any> | React.KeyboardEvent<any>) => void;
  selectNode: (e: React.MouseEvent<any> | React.KeyboardEvent<any>, nodeId: string) => void;
  isOpen: boolean;
  isSelected: boolean;
  explorerPath: ExplorerPath;
  onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
  viewType: 'tree' | 'group';
}) => {
  const isGroupNode = 'groupName' in node;
  const isLocationNode = 'locationName' in node;
  const isAssetNode = !isGroupNode && !isLocationNode;

  const displayName = React.useMemo(() => {
    if (isAssetNode) {
      return getDisplayName(node);
    } else if (isGroupNode) {
      return node.groupName;
    } else {
      return node.locationName;
    }
  }, [isAssetNode, isGroupNode, node]);

  const downstream = Object.keys(graphData.downstream[node.id] ?? {});
  const elementRef = React.useRef<HTMLDivElement | null>(null);

  const showArrow =
    !isAssetNode || (viewType === 'tree' && downstream.filter((id) => graphData.nodes[id]).length);

  const ref = React.useRef<HTMLButtonElement | null>(null);
  React.useLayoutEffect(() => {
    // When we click on a node in the graph it also changes "isSelected" in the sidebar.
    // We want to check if the focus is currently in the graph and if it is lets keep it there
    // Otherwise it means the click happened in the sidebar in which case we should move focus to the element
    // in the sidebar
    if (ref.current && isSelected && !isElementInsideSVGViewport(document.activeElement)) {
      ref.current.focus();
    }
  }, [isSelected]);

  return (
    <>
      <Box ref={elementRef} onClick={selectThisNode} padding={{left: 8}}>
        <BoxWrapper level={level}>
          <Box padding={{right: 12}} flex={{direction: 'row', alignItems: 'center'}}>
            {showArrow ? (
              <UnstyledButton
                $showFocusOutline
                onClick={(e) => {
                  e.stopPropagation();
                  toggleOpen();
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
            ) : (
              <div style={{width: 18}} />
            )}
            <GrayOnHoverBox
              onDoubleClick={toggleOpen}
              style={{
                width: '100%',
                borderRadius: '8px',
                ...(isSelected ? {background: colorBackgroundBlue()} : {}),
              }}
              $showFocusOutline={true}
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
                {isAssetNode ? <StatusDot node={node} /> : null}
                {isGroupNode ? <Icon name="asset_group" /> : null}
                {isLocationNode ? <Icon name="folder_open" /> : null}
                <MiddleTruncate text={displayName} />
              </div>
              {isAssetNode ? (
                <AssetNodePopoverMenu
                  graphData={fullAssetGraphData}
                  node={node}
                  selectNode={selectNode}
                  explorerPath={explorerPath}
                  onChangeExplorerPath={onChangeExplorerPath}
                />
              ) : null}
            </GrayOnHoverBox>
          </Box>
        </BoxWrapper>
      </Box>
    </>
  );
};

const AssetNodePopoverMenu = (props: Parameters<typeof useAssetNodeMenu>[0]) => {
  const {menu, dialog} = useAssetNodeMenu(props);
  return (
    <div
      onClick={(e) => {
        // stop propagation outside of the popover to prevent parent onClick from being selected
        e.stopPropagation();
      }}
      onKeyDown={(e) => {
        if (e.code === 'Space') {
          // Prevent the default scrolling behavior
          e.preventDefault();
        }
      }}
    >
      {dialog}
      <Popover
        content={menu}
        hoverOpenDelay={100}
        hoverCloseDelay={100}
        placement="right"
        shouldReturnFocusOnClose
        canEscapeKeyClose
      >
        <ExpandMore tabIndex={0} role="button">
          <Icon name="more_horiz" color={colorAccentGray()} />
        </ExpandMore>
      </Popover>
    </div>
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
            i < level - 1 ? {side: 'left', width: 1, color: colorKeylineDefault()} : undefined
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

const ExpandMore = styled.div``;

const GrayOnHoverBox = styled(UnstyledButton)`
  border-radius: 8px;
  cursor: pointer;
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
  &:hover,
  &:focus-within {
    background: ${colorBackgroundLight()};
    transition: background 100ms linear;
    ${ExpandMore} {
      visibility: visible;
    }
  }
  ${ExpandMore} {
    visibility: hidden;
  }
`;

function isElementInsideSVGViewport(element: Element | null) {
  return !!element?.closest('[data-svg-viewport]');
}
