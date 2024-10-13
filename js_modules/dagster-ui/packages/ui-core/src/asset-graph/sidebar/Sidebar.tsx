import {Box, Button, Icon, Skeleton, Tooltip} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';

import {AssetSidebarNode} from './AssetSidebarNode';
import {FolderNodeType, getDisplayName, nodePathKey} from './util';
import {LayoutContext} from '../../app/LayoutProvider';
import {AssetKey} from '../../assets/types';
import {useQueryAndLocalStoragePersistedState} from '../../hooks/useQueryAndLocalStoragePersistedState';
import {ExplorerPath} from '../../pipelines/PipelinePathUtils';
import {Container, Inner, Row} from '../../ui/VirtualizedTable';
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
          const nextOpsQuery = explorerPath.opsQuery.trim()
            ? `\"${tokenForAssetKey({path})}\"`
            : '*';
          onChangeExplorerPath(
            {
              ...explorerPath,
              opsQuery: nextOpsQuery,
            },
            'push',
          );
        } catch (e) {
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
        return new Set(qs['open-nodes']);
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
              getDisplayName(graphData.nodes[a]!),
              getDisplayName(graphData.nodes[b]!),
            ),
          ),
      [graphData],
    );

    const renderedNodes = React.useMemo(() => {
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
        if (!codeLocationNodes[codeLocation]!.groups[groupId]!) {
          groupsCount += 1;
        }
        codeLocationNodes[codeLocation]!.groups[groupId] = codeLocationNodes[codeLocation]!.groups[
          groupId
        ] || {
          groupName,
          assets: [],
          repositoryName,
          repositoryLocationName: locationName,
        };
        codeLocationNodes[codeLocation]!.groups[groupId]!.assets.push(node);
      });
      const codeLocationsCount = Object.keys(codeLocationNodes).length;
      Object.entries(codeLocationNodes)
        .sort(([_1, a], [_2, b]) => COLLATOR.compare(a.locationName, b.locationName))
        .forEach(([locationName, locationNode]) => {
          folderNodes.push({locationName, id: locationName, level: 1});
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
    }, [
      lastSelectedNode,
      graphData,
      // eslint-disable-next-line react-hooks/exhaustive-deps
      lastSelectedNode &&
        renderedNodes.findIndex((node) => nodePathKey(lastSelectedNode) === nodePathKey(node)),
    ]);

    const indexOfLastSelectedNode = React.useMemo(
      () => {
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
      },
      // eslint-disable-next-line react-hooks/exhaustive-deps
      [renderedNodes, selectedNode],
    );
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
          border="bottom"
        >
          <SearchFilter
            values={React.useMemo(() => {
              return allAssetKeys.map((key) => ({
                value: JSON.stringify(key.path),
                label: key.path[key.path.length - 1]!,
              }));
            }, [allAssetKeys])}
            onSelectValue={selectNode}
          />
          <Tooltip content="Hide sidebar">
            <Button icon={<Icon name="panel_show_right" />} onClick={hideSidebar} />
          </Tooltip>
        </Box>
        <div>
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
              <Inner $totalHeight={totalHeight}>
                {items.map(({index, key, size, start}) => {
                  const node = renderedNodes[index]!;
                  const isCodelocationNode = 'locationName' in node;
                  const isGroupNode = 'groupNode' in node;
                  const row = !isCodelocationNode && !isGroupNode ? graphData.nodes[node.id] : node;
                  const isSelected =
                    selectedNode?.id === node.id || selectedNodes.includes(row as GraphNode);
                  return (
                    <Row $height={size} $start={start} key={key} data-key={key}>
                      <AssetSidebarNode
                        isOpen={openNodes.has(nodePathKey(node))}
                        fullAssetGraphData={fullAssetGraphData}
                        node={row!}
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
                    </Row>
                  );
                })}
              </Inner>
            </Container>
          )}
        </div>
      </div>
    );
  },
);
