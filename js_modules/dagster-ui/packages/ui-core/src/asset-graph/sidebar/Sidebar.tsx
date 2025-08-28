import {Box} from '@dagster-io/ui-components';
import * as React from 'react';
import {useMemo} from 'react';

import {AssetSidebarListView} from './AssetSidebarListView';
import {SearchInput} from './SearchInput';
import {SidebarHeader} from './SidebarHeader';
import {TreeViewPanel} from './TreeViewPanel';
import {
  buildFolderNodes,
  buildTreeNodesLeafToRoot,
  buildTreeNodesRootToLeaf,
  getLeafNodes,
  getRootNodes,
} from './treeBuilders';
import {useSidebarSelectionState} from './useSidebarSelectionState';
import {LayoutContext} from '../../app/LayoutProvider';
import {usePrefixedCacheKey} from '../../app/usePrefixedCacheKey';
import {AssetKey} from '../../assets/types';
import {useQueryAndLocalStoragePersistedState} from '../../hooks/useQueryAndLocalStoragePersistedState';
import {ExplorerPath} from '../../pipelines/PipelinePathUtils';
import {buildRepoPathForHuman} from '../../workspace/buildRepoAddress';
import {AssetGroup} from '../AssetGraphExplorer';
import {AssetGraphViewType, GraphData, GraphNode} from '../Utils';

interface AssetGraphExplorerSidebarProps {
  assetGraphData: GraphData;
  fullAssetGraphData: GraphData;
  selectedNodes: GraphNode[];
  selectNode: (e: React.MouseEvent<any> | React.KeyboardEvent<any>, nodeId: string) => void;
  explorerPath: ExplorerPath;
  onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
  allAssetKeys: AssetKey[];
  expandedGroups: string[];
  setExpandedGroups: (a: string[]) => void;
  hideSidebar: () => void;
  viewType: AssetGraphViewType;
  onFilterToGroup: (group: AssetGroup) => void;
  loading: boolean;
}

export const AssetGraphExplorerSidebar = React.memo(
  ({
    assetGraphData,
    fullAssetGraphData,
    selectedNodes,
    selectNode: _selectNode,
    explorerPath,
    onChangeExplorerPath,
    allAssetKeys,
    hideSidebar,
    viewType,
    onFilterToGroup,
    loading,
  }: AssetGraphExplorerSidebarProps) => {
    const lastSelectedNode = selectedNodes[selectedNodes.length - 1];
    // In the empty stay when no query is typed use the full asset graph data to populate the sidebar
    const graphData = Object.keys(assetGraphData.nodes).length
      ? assetGraphData
      : fullAssetGraphData;
    const [selectWhenDataAvailable, setSelectWhenDataAvailable] = React.useState<
      [React.MouseEvent<any> | React.KeyboardEvent<any>, string] | null
    >(null);
    const selectedNodeHasDataAvailable = selectWhenDataAvailable
      ? !!graphData.nodes[selectWhenDataAvailable[1]]
      : false;

    React.useEffect(() => {
      if (selectWhenDataAvailable && selectedNodeHasDataAvailable) {
        const [e, id] = selectWhenDataAvailable;
        _selectNode(e, id);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectWhenDataAvailable, selectedNodeHasDataAvailable]);

    const selectNode = (
      e: React.MouseEvent<any> | React.KeyboardEvent<any>,
      id: string,
      sidebarNodeInfo?: {path: string; direction: 'root-to-leaf' | 'leaf-to-root'} | undefined,
    ) => {
      if (sidebarNodeInfo) {
        if (sidebarNodeInfo.direction === 'root-to-leaf') {
          setLastSelectedSidebarNodeRootToLeaf({id, path: sidebarNodeInfo.path});
        } else {
          setLastSelectedSidebarNodeLeafToRoot({id, path: sidebarNodeInfo.path});
        }
      }
      setSelectWhenDataAvailable([e, id]);
      if (!assetGraphData.nodes[id]) {
        try {
          // If the graph data is not available then the current asset selection is filtering it out.
          // Change the asset selection to show all assets so that we can select the node.
          onChangeExplorerPath(
            {
              ...explorerPath,
              opsQuery: '*',
            },
            'push',
          );
        } catch {
          // Ignore errors. The selected node might be a group or code location so trying to JSON.parse the id will error.
          // For asset nodes the id is always a JSON array
        }
      }
    };

    const [sidebarViewType, setSidebarViewType] = useQueryAndLocalStoragePersistedState<
      'tree' | 'group'
    >({
      localStorageKey: usePrefixedCacheKey('asset-graph-sidebar-view-type'),
      encode: (val) => ({viewType: val}),
      decode: (val) => {
        if (val.viewType === 'tree' || val.viewType === 'group') {
          return val.viewType;
        }
        return 'group';
      },
      isEmptyState: (val) => val === null || val === 'group',
    });

    const {
      selectedNodeRootToLeaf,
      setSelectedNodeRootToLeaf,
      selectedNodeLeafToRoot,
      setSelectedNodeLeafToRoot,
      openNodesRootToLeaf,
      setOpenNodesRootToLeaf,
      openNodesLeafToRoot,
      setOpenNodesLeafToRoot,
      collapseAllNodes,
      setLastSelectedSidebarNodeRootToLeaf,
      setLastSelectedSidebarNodeLeafToRoot,
    } = useSidebarSelectionState({
      lastSelectedNode,
      graphData,
      sidebarViewType,
      buildRepoPathForHuman,
    });

    const rootNodes = React.useMemo(() => getRootNodes(graphData), [graphData]);
    const leafNodes = React.useMemo(() => getLeafNodes(graphData), [graphData]);

    const treeNodesRootToLeaf = React.useMemo(
      () => buildTreeNodesRootToLeaf(graphData, rootNodes, openNodesRootToLeaf),
      [graphData, rootNodes, openNodesRootToLeaf],
    );

    const treeNodesLeafToRoot = React.useMemo(
      () => buildTreeNodesLeafToRoot(graphData, leafNodes, openNodesLeafToRoot),
      [graphData, leafNodes, openNodesLeafToRoot],
    );

    const folderNodes = React.useMemo(
      () => buildFolderNodes(graphData, openNodesRootToLeaf),
      [graphData, openNodesRootToLeaf],
    );

    const renderedNodesRootToLeaf = sidebarViewType === 'tree' ? treeNodesRootToLeaf : folderNodes;
    const renderedNodesLeafToRoot = treeNodesLeafToRoot; // Leaf-to-root only supports tree view

    const {nav} = React.useContext(LayoutContext);

    React.useEffect(() => {
      if (viewType === 'global') {
        nav.close();
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [viewType]);

    const [expandedPanel, setExpandedPanel] = React.useState<'bottom' | 'top' | null>(null);

    const isTopPanelHidden = expandedPanel === 'bottom';
    const isBottomPanelHidden = expandedPanel === 'top';
    const treeViewRows = useMemo(() => {
      if (expandedPanel === 'top') {
        return 'minmax(0, 1fr) auto';
      } else if (expandedPanel === 'bottom') {
        return 'auto minmax(0, 1fr)';
      }
      return 'repeat(2, minmax(0, 1fr))';
    }, [expandedPanel]);

    return (
      <div
        style={{
          display: 'grid',
          gridTemplateRows: 'auto auto minmax(0, 1fr)',
          height: '100%',
        }}
      >
        <SidebarHeader
          sidebarViewType={sidebarViewType}
          setSidebarViewType={setSidebarViewType}
          hideSidebar={hideSidebar}
        />
        <SearchInput allAssetKeys={allAssetKeys} selectNode={selectNode} />
        {sidebarViewType === 'tree' ? (
          <div style={{display: 'grid', gridTemplateRows: treeViewRows}}>
            <TreeViewPanel
              title="Downstream"
              tooltipContent="Parent asset to child assets"
              expandedPanel={expandedPanel}
              setExpandedPanel={setExpandedPanel}
              position="top"
              isHidden={isTopPanelHidden}
              loading={loading}
              renderedNodes={renderedNodesRootToLeaf}
              graphData={graphData}
              fullAssetGraphData={fullAssetGraphData}
              selectedNodes={selectedNodes}
              selectedNode={selectedNodeRootToLeaf}
              lastSelectedNode={lastSelectedNode}
              openNodes={openNodesRootToLeaf}
              setOpenNodes={setOpenNodesRootToLeaf}
              collapseAllNodes={collapseAllNodes}
              setSelectedNode={setSelectedNodeRootToLeaf}
              selectNode={selectNode}
              explorerPath={explorerPath}
              onChangeExplorerPath={onChangeExplorerPath}
              onFilterToGroup={onFilterToGroup}
              viewType={sidebarViewType}
              direction="root-to-leaf"
            />
            <TreeViewPanel
              title="Upstream"
              tooltipContent="Child asset to parent assets"
              expandedPanel={expandedPanel}
              setExpandedPanel={setExpandedPanel}
              position="bottom"
              isHidden={isBottomPanelHidden}
              loading={loading}
              renderedNodes={renderedNodesLeafToRoot}
              graphData={graphData}
              fullAssetGraphData={fullAssetGraphData}
              selectedNodes={selectedNodes}
              selectedNode={selectedNodeLeafToRoot}
              lastSelectedNode={lastSelectedNode}
              openNodes={openNodesLeafToRoot}
              setOpenNodes={setOpenNodesLeafToRoot}
              collapseAllNodes={collapseAllNodes}
              setSelectedNode={setSelectedNodeLeafToRoot}
              selectNode={selectNode}
              explorerPath={explorerPath}
              onChangeExplorerPath={onChangeExplorerPath}
              onFilterToGroup={onFilterToGroup}
              viewType={sidebarViewType}
              direction="leaf-to-root"
            />
          </div>
        ) : (
          <Box border="top" padding={{top: 4}}>
            <AssetSidebarListView
              loading={loading}
              renderedNodes={renderedNodesRootToLeaf}
              graphData={graphData}
              fullAssetGraphData={fullAssetGraphData}
              selectedNodes={selectedNodes}
              selectedNode={selectedNodeRootToLeaf}
              lastSelectedNode={lastSelectedNode}
              openNodes={openNodesRootToLeaf}
              setOpenNodes={setOpenNodesRootToLeaf}
              setSelectedNode={setSelectedNodeRootToLeaf}
              selectNode={selectNode}
              explorerPath={explorerPath}
              onChangeExplorerPath={onChangeExplorerPath}
              onFilterToGroup={onFilterToGroup}
              viewType={sidebarViewType}
            />
          </Box>
        )}
      </div>
    );
  },
);
