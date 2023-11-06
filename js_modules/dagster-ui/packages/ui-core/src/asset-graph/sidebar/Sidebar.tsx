import {Box, Button, Colors, Icon, ButtonGroup, Tooltip} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React from 'react';
import styled from 'styled-components';

import {AssetKey} from '../../assets/types';
import {ExplorerPath} from '../../pipelines/PipelinePathUtils';
import {Container, Inner, Row} from '../../ui/VirtualizedTable';
import {buildRepoPathForHuman} from '../../workspace/buildRepoAddress';
import {GraphData, GraphNode, tokenForAssetKey} from '../Utils';
import {SearchFilter} from '../sidebar/SearchFilter';

import {Node} from './Node';
import {FolderNodeType, TreeNodeType, getDisplayName, nodePathKey} from './util';

const COLLATOR = new Intl.Collator(navigator.language, {sensitivity: 'base', numeric: true});

export const AssetGraphExplorerSidebar = React.memo(
  ({
    assetGraphData,
    fullAssetGraphData,
    lastSelectedNode,
    selectNode: _selectNode,
    explorerPath,
    onChangeExplorerPath,
    allAssetKeys,
    hideSidebar,
  }: {
    assetGraphData: GraphData;
    fullAssetGraphData: GraphData;
    lastSelectedNode: GraphNode;
    selectNode: (e: React.MouseEvent<any> | React.KeyboardEvent<any>, nodeId: string) => void;
    explorerPath: ExplorerPath;
    onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
    allAssetKeys: AssetKey[];
    expandedGroups: string[];
    setExpandedGroups: (a: string[]) => void;
    hideSidebar: () => void;
  }) => {
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
    const [openNodes, setOpenNodes] = React.useState<Set<string>>(new Set());
    const [selectedNode, setSelectedNode] = React.useState<
      null | {id: string; path: string} | {id: string}
    >(null);

    const [viewType, setViewType] = React.useState<'tree' | 'group'>('group');

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

    const treeNodes = React.useMemo(() => {
      const queue = rootNodes.map((id) => ({level: 1, id, path: id}));

      const treeNodes: TreeNodeType[] = [];
      while (queue.length) {
        const node = queue.shift()!;
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

    const {folderNodes, codeLocationNodes} = React.useMemo(() => {
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
              assets: string[];
            }
          >;
        }
      > = {};
      Object.entries(graphData.nodes).forEach(([id, node]) => {
        const locationName = node.definition.repository.location.name;
        const repositoryName = node.definition.repository.name;
        const groupName = node.definition.groupName || 'default';
        const codeLocation = buildRepoPathForHuman(repositoryName, locationName);
        codeLocationNodes[codeLocation] = codeLocationNodes[codeLocation] || {
          locationName: codeLocation,
          groups: {},
        };
        codeLocationNodes[codeLocation]!.groups[groupName] = codeLocationNodes[codeLocation]!
          .groups[groupName] || {
          groupName,
          assets: [],
        };
        codeLocationNodes[codeLocation]!.groups[groupName]!.assets.push(id);
      });
      Object.entries(codeLocationNodes).forEach(([locationName, locationNode]) => {
        folderNodes.push({locationName, id: locationName, level: 1});
        if (openNodes.has(locationName)) {
          Object.entries(locationNode.groups).forEach(([groupName, groupNode]) => {
            const groupId = locationName + ':' + groupName;
            folderNodes.push({groupName, id: groupId, level: 2});
            if (openNodes.has(groupId)) {
              groupNode.assets
                .sort((a, b) => COLLATOR.compare(a, b))
                .forEach((assetKey) => {
                  folderNodes.push({
                    id: assetKey,
                    path: locationName + ':' + groupName + ':' + assetKey,
                    level: 3,
                  });
                });
            }
          });
        }
      });

      return {folderNodes, codeLocationNodes};
    }, [graphData.nodes, openNodes]);

    const renderedNodes = viewType === 'tree' ? treeNodes : folderNodes;

    const containerRef = React.useRef<HTMLDivElement | null>(null);

    const rowVirtualizer = useVirtualizer({
      count: renderedNodes.length,
      getScrollElement: () => containerRef.current,
      estimateSize: () => 28,
      overscan: 10,
    });

    const totalHeight = rowVirtualizer.getTotalSize();
    const items = rowVirtualizer.getVirtualItems();

    React.useLayoutEffect(() => {
      if (renderedNodes.length === 1 && viewType === 'group') {
        // If there's a single code location and a single group in it then just open them
        setOpenNodes((prevOpenNodes) => {
          const nextOpenNodes = new Set(prevOpenNodes);
          const locations = Object.keys(codeLocationNodes);
          if (locations.length === 1) {
            const location = codeLocationNodes[locations[0]!]!;
            nextOpenNodes.add(location.locationName);
            const groups = Object.keys(location.groups);
            if (groups.length === 1) {
              nextOpenNodes.add(
                location.locationName + ':' + location.groups[groups[0]!]!.groupName,
              );
            }
          }
          return nextOpenNodes;
        });
      }
      if (lastSelectedNode) {
        setOpenNodes((prevOpenNodes) => {
          if (viewType === 'group') {
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
          }
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

          const nextOpenNodes = new Set(prevOpenNodes);

          const nodesInPath = path.split(':');
          let currentPath = nodesInPath[0]!;

          nextOpenNodes.add(currentPath);
          for (let i = 1; i < nodesInPath.length; i++) {
            currentPath = `${currentPath}:${nodesInPath[i]}`;
            nextOpenNodes.add(currentPath);
          }
          if (selectedNode?.id !== lastSelectedNode.id) {
            setSelectedNode({id: lastSelectedNode.id, path: currentPath});
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
      viewType,
      // eslint-disable-next-line react-hooks/exhaustive-deps
      lastSelectedNode &&
        renderedNodes.findIndex((node) => nodePathKey(lastSelectedNode) === nodePathKey(node)),
    ]);

    const indexOfLastSelectedNode = React.useMemo(
      () => {
        if (!selectedNode) {
          return -1;
        }
        if (viewType === 'tree') {
          return 'path' in selectedNode
            ? renderedNodes.findIndex((node) => 'path' in node && node.path === selectedNode.path)
            : -1;
        } else {
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
        }
      },
      // eslint-disable-next-line react-hooks/exhaustive-deps
      [viewType, renderedNodes, selectedNode],
    );
    const indexOfLastSelectedNodeRef = React.useRef(indexOfLastSelectedNode);
    indexOfLastSelectedNodeRef.current = indexOfLastSelectedNode;

    React.useLayoutEffect(() => {
      if (indexOfLastSelectedNode !== -1) {
        rowVirtualizer.scrollToIndex(indexOfLastSelectedNode, {
          align: 'center',
          smoothScroll: true,
        });
      }
      // Only scroll if the rootNodes changes or the selected node changes
      // otherwise opening/closing nodes will cause us to scroll again because the index changes
      // if we toggle a node above the selected node
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedNode, rootNodes, rowVirtualizer]);

    return (
      <div style={{display: 'grid', gridTemplateRows: 'auto auto minmax(0, 1fr)', height: '100%'}}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr auto',
            gap: '6px',
            padding: '12px 24px',
            paddingRight: 12,
            borderBottom: `1px solid ${Colors.KeylineGray}`,
          }}
        >
          <ButtonGroupWrapper>
            <ButtonGroup
              activeItems={new Set([viewType])}
              buttons={[
                {id: 'group', label: 'Group view', icon: 'asset_group'},
                {id: 'tree', label: 'Tree view', icon: 'gantt_flat'},
              ]}
              onClick={(id: 'tree' | 'group') => {
                setViewType(id);
              }}
            />
          </ButtonGroupWrapper>
          <Tooltip content="Hide sidebar">
            <Button icon={<Icon name="panel_show_right" />} onClick={hideSidebar} />
          </Tooltip>
        </div>
        <Box padding={{vertical: 8, left: 24, right: 12}}>
          <SearchFilter
            values={React.useMemo(() => {
              return allAssetKeys.map((key) => ({
                value: JSON.stringify(key.path),
                label: key.path[key.path.length - 1]!,
              }));
            }, [allAssetKeys])}
            onSelectValue={selectNode}
          />
        </Box>
        <div>
          <Container
            ref={containerRef}
            onKeyDown={(e) => {
              let nextIndex = 0;
              if (e.code === 'ArrowDown' || e.code === 'ArrowUp') {
                nextIndex = indexOfLastSelectedNodeRef.current + (e.code === 'ArrowDown' ? 1 : -1);
                indexOfLastSelectedNodeRef.current = nextIndex;
                e.preventDefault();
                const nextNode = renderedNodes[nextIndex % renderedNodes.length]!;
                setSelectedNode(nextNode);
                selectNode(e, nextNode.id);
              } else if (e.code === 'ArrowLeft' || e.code === 'ArrowRight') {
                const open = e.code === 'ArrowRight';
                setOpenNodes((nodes) => {
                  const node = renderedNodes[indexOfLastSelectedNode];
                  if (!node) {
                    return nodes;
                  }
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
              {items.map(({index, key, size, start, measureElement}) => {
                const node = renderedNodes[index]!;
                const isCodelocationNode = 'locationName' in node;
                const isGroupNode = 'groupName' in node;
                const row = !isCodelocationNode && !isGroupNode ? graphData.nodes[node.id] : node;
                return (
                  <Row
                    $height={size}
                    $start={start}
                    key={key}
                    style={{overflow: 'visible'}}
                    ref={measureElement}
                  >
                    {row ? (
                      <Node
                        viewType={viewType}
                        isOpen={openNodes.has(nodePathKey(node))}
                        graphData={graphData}
                        fullAssetGraphData={fullAssetGraphData}
                        node={row}
                        level={node.level}
                        isSelected={
                          selectedNode && 'path' in node && 'path' in selectedNode
                            ? selectedNode.path === node.path
                            : selectedNode?.id === node.id
                        }
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
                      />
                    ) : null}
                  </Row>
                );
              })}
            </Inner>
          </Container>
        </div>
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
