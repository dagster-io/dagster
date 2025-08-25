import {Box, Button, ButtonGroup, Icon, Tooltip} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {AssetSidebarListView} from './AssetSidebarListView';
import {FolderNodeType, TreeNodeType, getDisplayName} from './util';
import {LayoutContext} from '../../app/LayoutProvider';
import {usePrefixedCacheKey} from '../../app/usePrefixedCacheKey';
import {AssetKey} from '../../assets/types';
import {useQueryAndLocalStoragePersistedState} from '../../hooks/useQueryAndLocalStoragePersistedState';
import {ExplorerPath} from '../../pipelines/PipelinePathUtils';
import {buildRepoPathForHuman} from '../../workspace/buildRepoAddress';
import {AssetGroup} from '../AssetGraphExplorer';
import {AssetGraphViewType, GraphData, GraphNode, groupIdForNode, tokenForAssetKey} from '../Utils';
import {SearchFilter} from '../sidebar/SearchFilter';

const COLLATOR = new Intl.Collator(navigator.language, {sensitivity: 'base', numeric: true});

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
  }: {
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
  }) => {
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
      if (selectWhenDataAvailable) {
        const [e, id] = selectWhenDataAvailable;
        _selectNode(e, id);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectWhenDataAvailable, selectedNodeHasDataAvailable]);

    const selectNode: typeof _selectNode = (e, id) => {
      setSelectWhenDataAvailable([e, id]);
      if (!assetGraphData.nodes[id]) {
        try {
          const path = JSON.parse(id);
          let nextOpsQuery = explorerPath.opsQuery.trim();
          if (explorerPath.opsQuery.trim()) {
            nextOpsQuery = `key:\"${tokenForAssetKey({path})}\"`;
          } else {
            nextOpsQuery = '*';
          }
          onChangeExplorerPath(
            {
              ...explorerPath,
              opsQuery: nextOpsQuery,
            },
            'push',
          );
        } catch {
          // Ignore errors. The selected node might be a group or code location so trying to JSON.parse the id will error.
          // For asset nodes the id is always a JSON array
        }
      }
    };
    const [openNodes, setOpenNodes] = React.useState<Set<string>>(() => new Set());
    const [selectedNode, setSelectedNode] = React.useState<
      null | {id: string; path: string} | {id: string}
    >(null);

    const [sidebarViewType, setSidebarViewType] = useQueryAndLocalStoragePersistedState<
      'tree' | 'group'
    >({
      localStorageKey: usePrefixedCacheKey('asset-graph-sidebar-view-type'),
      encode: (val) => ({viewType: val}),
      decode: (val) => {
        if (val.viewType === 'tree' || val.viewType === 'group') {
          return val.viewType;
        }
        return 'tree';
      },
      isEmptyState: (val) => val === null || val === 'tree',
    });

    const rootNodes = React.useMemo(
      () =>
        Object.keys(graphData.nodes)
          .filter(
            (id) =>
              // When we filter to a subgraph, the nodes at the root aren't real roots, but since
              // their upstream graph is cutoff we want to show them as roots in the sidebar.
              // Find these nodes by filtering on whether there parent nodes are in assetGraphData
              !Object.keys(graphData.upstream[id] ?? {}).filter((id) => graphData.nodes[id]).length,
          )
          .sort((a, b) =>
            COLLATOR.compare(
              // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
              getDisplayName(graphData.nodes[a]!),
              // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
              getDisplayName(graphData.nodes[b]!),
            ),
          ),
      [graphData],
    );

    const treeNodes = React.useMemo(() => {
      const queue = rootNodes.map((id) => ({level: 1, id, path: id}));

      const treeNodes: TreeNodeType[] = [];
      while (true) {
        const node = queue.shift();
        if (!node) {
          break;
        }
        treeNodes.push(node);
        if (openNodes.has(node.path)) {
          const downstream = Object.keys(graphData.downstream[node.id] || {}).filter(
            (id) => graphData.nodes[id],
          );
          queue.unshift(
            ...downstream.map((id) => ({level: node.level + 1, id, path: `${node.path}:${id}`})),
          );
        }
      }
      return treeNodes;
    }, [graphData.downstream, graphData.nodes, openNodes, rootNodes]);

    const folderNodes = React.useMemo(() => {
      const folderNodes: FolderNodeType[] = [];

      // Map of Code Locations -> Groups -> Assets
      const codeLocationNodes: Record<
        string,
        {
          locationName: string;
          groups: Record<
            string,
            {
              groupName: string;
              assets: GraphNode[];
              repositoryName: string;
              repositoryLocationName: string;
            }
          >;
        }
      > = {};

      let groupsCount = 0;
      Object.values(graphData.nodes).forEach((node) => {
        const locationName = node.definition.repository.location.name;
        const repositoryName = node.definition.repository.name;
        const groupName = node.definition.groupName || 'default';
        const groupId = groupIdForNode(node);
        const codeLocation = buildRepoPathForHuman(repositoryName, locationName);
        codeLocationNodes[codeLocation] = codeLocationNodes[codeLocation] || {
          locationName: codeLocation,
          groups: {},
        };
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        if (!codeLocationNodes[codeLocation]!.groups[groupId]!) {
          groupsCount += 1;
        }
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        codeLocationNodes[codeLocation]!.groups[groupId] = codeLocationNodes[codeLocation]!.groups[
          groupId
        ] || {
          groupName,
          assets: [],
          repositoryName,
          repositoryLocationName: locationName,
        };
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        codeLocationNodes[codeLocation]!.groups[groupId]!.assets.push(node);
      });
      const codeLocationsCount = Object.keys(codeLocationNodes).length;
      Object.entries(codeLocationNodes)
        .sort(([_1, a], [_2, b]) => COLLATOR.compare(a.locationName, b.locationName))
        .forEach(([locationName, locationNode]) => {
          folderNodes.push({
            locationName,
            id: locationName,
            level: 1,
            openAlways: codeLocationsCount === 1,
          });
          if (openNodes.has(locationName) || codeLocationsCount === 1) {
            Object.entries(locationNode.groups)
              .sort(([_1, a], [_2, b]) => COLLATOR.compare(a.groupName, b.groupName))
              .forEach(([id, groupNode]) => {
                folderNodes.push({
                  groupNode,
                  id,
                  level: 2,
                });
                if (openNodes.has(id) || groupsCount === 1) {
                  groupNode.assets
                    .sort((a, b) => COLLATOR.compare(a.id, b.id))
                    .forEach((assetNode) => {
                      folderNodes.push({
                        id: assetNode.id,
                        path: [
                          locationName,
                          groupNode.groupName,
                          tokenForAssetKey(assetNode.assetKey),
                        ].join(':'),
                        level: 3,
                      });
                    });
                }
              });
          }
        });

      if (groupsCount === 1) {
        return folderNodes
          .filter((node) => node.level === 3)
          .map((node) => ({
            ...node,
            level: 1,
          }));
      }

      return folderNodes;
    }, [graphData.nodes, openNodes]);

    const renderedNodes = sidebarViewType === 'tree' ? treeNodes : folderNodes;

    const {nav} = React.useContext(LayoutContext);

    React.useEffect(() => {
      if (viewType === 'global') {
        nav.close();
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [viewType]);

    React.useLayoutEffect(() => {
      if (lastSelectedNode) {
        setOpenNodes((prevOpenNodes) => {
          if (sidebarViewType === 'tree') {
            let path = lastSelectedNode.id;
            let currentId = lastSelectedNode.id;
            let next: string | undefined;
            while ((next = Object.keys(graphData.upstream[currentId] ?? {})[0])) {
              if (!graphData.nodes[next]) {
                break;
              }
              path = `${next}:${path}`;
              currentId = next;
            }

            const nodesInPath = path.split(':');
            let currentPath = nodesInPath[0];

            if (!currentPath) {
              return prevOpenNodes;
            }

            const nextOpenNodes = new Set(prevOpenNodes);
            nextOpenNodes.add(currentPath);
            for (let i = 1; i < nodesInPath.length; i++) {
              currentPath = `${currentPath}:${nodesInPath[i]}`;
              nextOpenNodes.add(currentPath);
            }
            if (selectedNode?.id !== lastSelectedNode.id) {
              setSelectedNode({id: lastSelectedNode.id, path: currentPath});
            }
            return nextOpenNodes;
          }
          const nextOpenNodes = new Set(prevOpenNodes);
          const assetNode = graphData.nodes[lastSelectedNode.id];
          if (assetNode) {
            const locationName = buildRepoPathForHuman(
              assetNode.definition.repository.name,
              assetNode.definition.repository.location.name,
            );
            const groupName = assetNode.definition.groupName || 'default';
            nextOpenNodes.add(locationName);
            nextOpenNodes.add(locationName + ':' + groupName);
          }
          if (selectedNode?.id !== lastSelectedNode.id) {
            setSelectedNode({id: lastSelectedNode.id});
          }
          return nextOpenNodes;
        });
      } else {
        setSelectedNode(null);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [lastSelectedNode, graphData]);

    return (
      <div style={{display: 'grid', gridTemplateRows: 'auto auto minmax(0, 1fr)', height: '100%'}}>
        <Box
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr auto',
            gap: '6px',
            padding: '12px 24px',
            paddingRight: 12,
          }}
        >
          <ButtonGroupWrapper>
            <ButtonGroup
              activeItems={new Set([sidebarViewType])}
              buttons={[
                {id: 'group', label: 'Group view', icon: 'asset_group'},
                {id: 'tree', label: 'Tree view', icon: 'gantt_flat'},
              ]}
              onClick={(id: 'tree' | 'group') => {
                setSidebarViewType(id);
              }}
            />
          </ButtonGroupWrapper>
          <Tooltip content="Hide sidebar">
            <Button icon={<Icon name="panel_show_right" />} onClick={hideSidebar} />
          </Tooltip>
        </Box>
        <Box padding={{vertical: 8, left: 24, right: 12}}>
          <SearchFilter
            values={React.useMemo(() => {
              return allAssetKeys.map((key) => ({
                value: JSON.stringify(key.path),
                // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                label: key.path[key.path.length - 1]!,
              }));
            }, [allAssetKeys])}
            onSelectValue={selectNode}
          />
        </Box>
        <Box border="top">
          <AssetSidebarListView
            loading={loading}
            renderedNodes={renderedNodes}
            graphData={graphData}
            fullAssetGraphData={fullAssetGraphData}
            selectedNodes={selectedNodes}
            selectedNode={selectedNode}
            lastSelectedNode={lastSelectedNode}
            openNodes={openNodes}
            setOpenNodes={setOpenNodes}
            setSelectedNode={setSelectedNode}
            selectNode={selectNode}
            explorerPath={explorerPath}
            onChangeExplorerPath={onChangeExplorerPath}
            onFilterToGroup={onFilterToGroup}
            viewType={sidebarViewType}
          />
        </Box>
      </div>
    );
  },
);

const ButtonGroupWrapper = styled.div`
  > * {
    display: grid;
    grid-template-columns: 1fr 1fr;
    > * {
      place-content: center;
    }
  }
`;
