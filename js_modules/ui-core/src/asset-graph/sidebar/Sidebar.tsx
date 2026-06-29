import {
  Box,
  Button,
  Container,
  Icon,
  Inner,
  Row,
  Skeleton,
  Tooltip,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';

import {AssetSidebarNode} from './AssetSidebarNode';
import {FolderNodeType, getDisplayName, nodePathKey} from './util';
import {LayoutContext} from '../../app/LayoutProvider';
import {useFeatureFlags} from '../../app/useFeatureFlags';
import {AssetKey} from '../../assets/types';
import {useQueryAndLocalStoragePersistedState} from '../../hooks/useQueryAndLocalStoragePersistedState';
import {ExplorerPath} from '../../pipelines/PipelinePathUtils';
import {invariant} from '../../util/invariant';
import {buildRepoPathForHuman} from '../../workspace/buildRepoAddress';
import {AssetGroup} from '../AssetGraphExplorer';
import {
  AssetGraphViewType,
  GraphData,
  GraphNode,
  ancestorGroupIds,
  groupIdForNode,
  parseGroupId,
  tokenForAssetKey,
} from '../Utils';
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
    hideSidebar: () => void;
    viewType: AssetGraphViewType;
    onFilterToGroup: (group: AssetGroup) => void;
    loading: boolean;
  }) => {
    const {flagAssetGraphGroupsPerCodeLocation} = useFeatureFlags();

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
    const [openNodes, setOpenNodes] = useQueryAndLocalStoragePersistedState<Set<string>>({
      // include pathname so that theres separate storage entries for graphs at different URLs
      // eg. independent group graph should persist open nodes separately
      localStorageKey: `asset-graph-open-sidebar-nodes-${viewType}-${explorerPath.pipelineName}`,
      encode: (val) => {
        return {'open-nodes': Array.from(val)};
      },
      decode: (qs) => {
        const openNodes = qs['open-nodes'];
        if (Array.isArray(openNodes)) {
          return new Set(openNodes.map((node) => String(node)));
        }
        return new Set();
      },
      isEmptyState: (val) => val.size === 0,
    });
    const [selectedNode, setSelectedNode] = React.useState<
      null | {id: string; path: string} | {id: string}
    >(null);

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

    const renderedNodes = React.useMemo(() => {
      return flagAssetGraphGroupsPerCodeLocation
        ? buildRenderedNodesWithCodeLocations(graphData.nodes, openNodes)
        : buildRenderedNodes(graphData.nodes, openNodes);
    }, [flagAssetGraphGroupsPerCodeLocation, graphData.nodes, openNodes]);

    const {nav} = React.useContext(LayoutContext);

    React.useEffect(() => {
      if (viewType === 'global') {
        nav.close();
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [viewType]);

    const containerRef = React.useRef<HTMLDivElement | null>(null);

    const rowVirtualizer = useVirtualizer({
      count: renderedNodes.length,
      getScrollElement: () => containerRef.current,
      estimateSize: () => 32,
      overscan: 10,
    });

    const totalHeight = rowVirtualizer.getTotalSize();
    const items = rowVirtualizer.getVirtualItems();

    React.useLayoutEffect(() => {
      if (lastSelectedNode) {
        setOpenNodes((prevOpenNodes) => {
          const nextOpenNodes = new Set(prevOpenNodes);
          const assetNode = graphData.nodes[lastSelectedNode.id];
          if (assetNode) {
            const locationName = buildRepoPathForHuman(
              assetNode.definition.repository.name,
              assetNode.definition.repository.location.name,
            );
            nextOpenNodes.add(locationName);
            // Use groupIdForNode (not locationName+:+groupName) so the keys match
            // the tree node ids that flattenGroupTree consults. Add every ancestor
            // too — flattenGroupTree won't descend past a closed parent.
            const leafGroupId = groupIdForNode(assetNode);
            nextOpenNodes.add(leafGroupId);
            for (const ancId of ancestorGroupIds(leafGroupId)) {
              nextOpenNodes.add(ancId);
            }
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
    }, [
      lastSelectedNode,
      graphData,
      // eslint-disable-next-line react-hooks/exhaustive-deps
      lastSelectedNode &&
        renderedNodes.findIndex((node) => nodePathKey(lastSelectedNode) === nodePathKey(node)),
    ]);

    const indexOfLastSelectedNode = React.useMemo(() => {
      if (!selectedNode) {
        return -1;
      }
      return renderedNodes.findIndex((node) => {
        // If you select a node via the search dropdown or from the graph directly then
        // selectedNode will have an `id` field and not a path. The nodes in renderedNodes
        // will always have a path so we need to explicitly check if the id's match
        if (!('path' in selectedNode)) {
          return node.id === selectedNode.id;
        } else {
          return nodePathKey(node) === nodePathKey(selectedNode);
        }
      });
    }, [renderedNodes, selectedNode]);
    const indexOfLastSelectedNodeRef = React.useRef(indexOfLastSelectedNode);
    indexOfLastSelectedNodeRef.current = indexOfLastSelectedNode;

    React.useLayoutEffect(() => {
      if (indexOfLastSelectedNode !== -1) {
        rowVirtualizer.scrollToIndex(indexOfLastSelectedNode, {
          align: 'center',
          behavior: 'smooth',
        });
      }
      // Only scroll if the rootNodes changes or the selected node changes
      // otherwise opening/closing nodes will cause us to scroll again because the index changes
      // if we toggle a node above the selected node
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedNode, rootNodes, rowVirtualizer]);

    return (
      <div style={{display: 'grid', gridTemplateRows: 'auto minmax(0, 1fr)', height: '100%'}}>
        <Box
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr auto',
            gap: '6px',
            padding: '12px 24px',
            paddingRight: 12,
          }}
        >
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
          <Tooltip content="Hide sidebar">
            <Button icon={<Icon name="panel_show_right" />} onClick={hideSidebar} />
          </Tooltip>
        </Box>
        <Box border="top">
          {loading ? (
            <Box flex={{direction: 'column', gap: 9}} padding={12}>
              <Skeleton $height={21} $width="50%" />
              <Skeleton $height={21} $width="80%" />
              <Skeleton $height={21} $width="65%" />
              <Skeleton $height={21} $width="90%" />
            </Box>
          ) : (
            <Container
              ref={containerRef}
              onKeyDown={(e) => {
                let nextIndex = 0;
                if (e.code === 'ArrowDown' || e.code === 'ArrowUp') {
                  nextIndex =
                    indexOfLastSelectedNodeRef.current + (e.code === 'ArrowDown' ? 1 : -1);
                  indexOfLastSelectedNodeRef.current = nextIndex;
                  e.preventDefault();
                  const nextNode =
                    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                    renderedNodes[(nextIndex + renderedNodes.length) % renderedNodes.length]!;
                  setSelectedNode(nextNode);
                  selectNode(e, nextNode.id);
                } else if (e.code === 'ArrowLeft' || e.code === 'ArrowRight') {
                  const open = e.code === 'ArrowRight';
                  const node = renderedNodes[indexOfLastSelectedNode];
                  if (!node || 'path' in node) {
                    return;
                  }
                  setOpenNodes((nodes) => {
                    const openNodes = new Set(nodes);
                    if (open) {
                      openNodes.add(nodePathKey(node));
                    } else {
                      openNodes.delete(nodePathKey(node));
                    }
                    return openNodes;
                  });
                }
              }}
            >
              <Inner totalHeight={totalHeight}>
                {items.map(({index, key, size, start}) => {
                  const node = renderedNodes[index];
                  invariant(node, 'Sidebar node is required');

                  const isCodeLocationNode = 'locationName' in node;
                  const isGroupNode = 'groupNode' in node;
                  const row = !isCodeLocationNode && !isGroupNode ? graphData.nodes[node.id] : node;
                  const isSelected =
                    selectedNode?.id === node.id || selectedNodes.includes(row as GraphNode);
                  invariant(row, 'Row for sidebar node is required');

                  return (
                    <Row height={size} start={start} key={key}>
                      <div data-index={index} ref={rowVirtualizer.measureElement}>
                        <AssetSidebarNode
                          isOpen={openNodes.has(nodePathKey(node))}
                          fullAssetGraphData={fullAssetGraphData}
                          node={row}
                          level={node.level}
                          isLastSelected={lastSelectedNode?.id === node.id}
                          isSelected={isSelected}
                          toggleOpen={() => {
                            setOpenNodes((nodes) => {
                              const openNodes = new Set(nodes);
                              const isOpen = openNodes.has(nodePathKey(node));
                              if (isOpen) {
                                openNodes.delete(nodePathKey(node));
                              } else {
                                openNodes.add(nodePathKey(node));
                              }
                              return openNodes;
                            });
                          }}
                          selectNode={(e, id) => {
                            selectNode(e, id);
                          }}
                          selectThisNode={(e) => {
                            setSelectedNode(node);
                            selectNode(e, node.id);
                          }}
                          explorerPath={explorerPath}
                          onChangeExplorerPath={onChangeExplorerPath}
                          onFilterToGroup={onFilterToGroup}
                        />
                      </div>
                    </Row>
                  );
                })}
              </Inner>
            </Container>
          )}
        </Box>
      </div>
    );
  },
);

// A node in the hierarchical group tree. `directAssets` holds assets whose
// group_name matches this node exactly, used to emit asset rows when the
// folder is open. `rolledUpAssets` includes all descendant assets, used for
// folder-row counts/statuses so a synthetic ancestor mirrors the graph view's
// collapsed-cluster rollup.
type GroupTreeNode = {
  id: string;
  segment: string;
  // Full hierarchical group name (e.g. `marketing/sales`), used for filter
  // strings so callers match the layout's GroupLayout.groupName convention.
  fullPath: string;
  repositoryName?: string;
  repositoryLocationName?: string;
  directAssets: GraphNode[];
  rolledUpAssets: GraphNode[];
  children: Map<string, GroupTreeNode>;
};

// Walks/creates a path from the root map to the leaf node for `groupId` and
// pushes `leafAssets` onto every visited node's `rolledUpAssets`, plus the
// leaf's `directAssets`. Returns the leaf node.
function addAssetsToGroupTree(
  rootMap: Map<string, GroupTreeNode>,
  groupId: string,
  fallback: {repositoryName?: string; repositoryLocationName?: string},
  leafAssets: GraphNode[],
): GroupTreeNode {
  const parsed = parseGroupId(groupId);
  const locationPrefix = parsed?.locationPrefix ?? '';
  const segments = parsed?.segments ?? [groupId];

  let cursor: Map<string, GroupTreeNode> = rootMap;
  let current: GroupTreeNode | undefined;
  let pathSoFar = '';
  for (const segment of segments) {
    pathSoFar = pathSoFar ? `${pathSoFar}/${segment}` : segment;
    // Key children by full id (locationPrefix + pathSoFar) so two code
    // locations both containing a top-level group named `marketing` don't
    // collide in the root map.
    const childId = `${locationPrefix}${pathSoFar}`;
    let child = cursor.get(childId);
    if (!child) {
      child = {
        id: childId,
        segment,
        fullPath: pathSoFar,
        ...fallback,
        directAssets: [],
        rolledUpAssets: [],
        children: new Map(),
      };
      cursor.set(childId, child);
    }
    child.rolledUpAssets.push(...leafAssets);
    current = child;
    cursor = child.children;
  }
  invariant(current, 'segments was empty — unreachable');
  current.directAssets.push(...leafAssets);
  return current;
}

function flattenGroupTree(
  roots: Map<string, GroupTreeNode>,
  openNodes: Set<string>,
  baseLevel: number,
  pathPrefix: string[],
  out: FolderNodeType[],
) {
  const sorted = Array.from(roots.values()).sort((a, b) => COLLATOR.compare(a.segment, b.segment));
  for (const node of sorted) {
    out.push({
      groupNode: {
        // Full path so onFilterToGroup builds a filter string matching the
        // layout's GroupLayout.groupName convention. Display strips this back
        // to the leaf segment via groupIdLeafName in AssetSidebarNode.
        groupName: node.fullPath,
        assets: node.rolledUpAssets,
        repositoryName: node.repositoryName,
        repositoryLocationName: node.repositoryLocationName,
      },
      id: node.id,
      level: baseLevel,
    });
    if (!openNodes.has(node.id)) {
      continue;
    }
    const assetLevel = baseLevel + 1;
    // Only emit direct asset rows so each asset appears exactly once in the
    // tree (otherwise an ancestor with rolled-up assets would duplicate every
    // descendant asset at its own level).
    [...node.directAssets]
      .sort((a, b) => COLLATOR.compare(a.id, b.id))
      .forEach((assetNode) => {
        out.push({
          id: assetNode.id,
          path: [...pathPrefix, node.segment, tokenForAssetKey(assetNode.assetKey)].join(':'),
          level: assetLevel,
        });
      });
    flattenGroupTree(node.children, openNodes, assetLevel, [...pathPrefix, node.segment], out);
  }
}

function buildRenderedNodes(nodes: {[assetId: string]: GraphNode}, openNodes: Set<string>) {
  const leafGroups: Record<string, {groupName: string; assets: GraphNode[]}> = {};

  Object.values(nodes).forEach((node) => {
    const groupName = node.definition.groupName || 'default';
    const groupId = groupIdForNode(node);
    leafGroups[groupId] = leafGroups[groupId] || {groupName, assets: []};
    leafGroups[groupId].assets.push(node);
  });

  const leafIds = Object.keys(leafGroups);
  const hasHierarchy = leafIds.some((id) => ancestorGroupIds(id).length > 0);
  const renderGroupsLayer = leafIds.length > 1 || hasHierarchy;

  if (!renderGroupsLayer) {
    const out: FolderNodeType[] = [];
    Object.entries(leafGroups).forEach(([_id, group]) => {
      [...group.assets]
        .sort((a, b) => COLLATOR.compare(a.id, b.id))
        .forEach((assetNode) => {
          out.push({
            id: assetNode.id,
            path: [group.groupName, tokenForAssetKey(assetNode.assetKey)].join(':'),
            level: 1,
          });
        });
    });
    return out;
  }

  const tree = new Map<string, GroupTreeNode>();
  Object.entries(leafGroups).forEach(([groupId, leaf]) => {
    addAssetsToGroupTree(tree, groupId, {}, leaf.assets);
  });

  const folderNodes: FolderNodeType[] = [];
  flattenGroupTree(tree, openNodes, 1, [], folderNodes);
  return folderNodes;
}

function buildRenderedNodesWithCodeLocations(
  nodes: {[assetId: string]: GraphNode},
  openNodes: Set<string>,
) {
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
  Object.values(nodes).forEach((node) => {
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
        const tree = new Map<string, GroupTreeNode>();
        Object.entries(locationNode.groups).forEach(([groupId, groupNode]) => {
          addAssetsToGroupTree(
            tree,
            groupId,
            {
              repositoryName: groupNode.repositoryName,
              repositoryLocationName: groupNode.repositoryLocationName,
            },
            groupNode.assets,
          );
        });
        flattenGroupTree(tree, openNodes, 2, [locationName], folderNodes);
      }
    });

  if (groupsCount === 1) {
    // Flatten away the wrapping location/group/folder layers and just show
    // the asset rows. Identify asset rows by the `path` field rather than a
    // fixed level (hierarchical group names push leaf assets to varying
    // depths, so the previous `level === 3` check missed them entirely).
    return folderNodes
      .filter((node): node is FolderNodeType & {path: string} => 'path' in node)
      .map((node) => ({...node, level: 1}));
  }

  return folderNodes;
}
