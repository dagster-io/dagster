import {Box, Colors, Icon} from '@dagster-io/ui-components';
import {assetHealthEnabled} from '@shared/app/assetHealthEnabled';
import * as React from 'react';

import {StatusDot, StatusDotNode} from './StatusDot';
import sidebarStyles from './css/AssetSidebarNode.module.css';
import {
  FolderNodeCodeLocationType,
  FolderNodeGroupType,
  FolderNodeNonAssetType,
  getDisplayName,
} from './util';
import {AssetHealthSummary} from '../../assets/AssetHealthSummary';
import {ExplorerPath} from '../../pipelines/PipelinePathUtils';
import {FocusableLabelContainer} from '../../ui/Sidebar/FocusableLabelContainer';
import {SidebarDisclosureTriangle} from '../../ui/Sidebar/SidebarDisclosureTriangle';
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

  const showArrow = !isAssetNode && !('openAlways' in node && node.openAlways);

  return (
    <Box ref={elementRef} padding={{left: 8, right: 12}}>
      <BoxWrapper level={level}>
        <Box
          className={sidebarStyles.itemContainer}
          flex={{direction: 'row', alignItems: 'center'}}
          onClick={selectThisNode}
          onDoubleClick={(e) => !e.metaKey && toggleOpen()}
        >
          {showArrow ? (
            <SidebarDisclosureTriangle isOpen={isOpen} toggleOpen={toggleOpen} />
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
        </Box>
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
        icon={
          assetHealthEnabled() ? (
            <div style={{marginLeft: -8, marginRight: -8}}>
              <AssetHealthSummary iconOnly assetKey={node.assetKey} />
            </div>
          ) : (
            <StatusDot node={node} />
          )
        }
        text={getDisplayName(node)}
      />
      <button className={sidebarStyles.expandMore} onClick={triggerContextMenu}>
        <Icon name="more_horiz" color={Colors.accentGray()} />
      </button>
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
      <button className={sidebarStyles.expandMore} onClick={triggerContextMenu}>
        <Icon name="more_horiz" color={Colors.accentGray()} />
      </button>
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
