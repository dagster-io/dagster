import {Button, Colors, Icon, Tooltip} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React from 'react';

import {AssetKey} from '../../assets/types';
import {ExplorerPath} from '../../pipelines/PipelinePathUtils';
import {Container, Inner, Row} from '../../ui/VirtualizedTable';
import {buildRepoPathForHuman} from '../../workspace/buildRepoAddress';
import {GraphData, GraphNode, tokenForAssetKey} from '../Utils';
import {SearchFilter} from '../sidebar/SearchFilter';

import {AssetSidebarNode} from './AssetSidebarNode';
import {FolderNodeType, getDisplayName, nodePathKey} from './util';

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
    const [openNodes, setOpenNodes] = React.useState<Set<string>>(new Set());
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

    const renderedNodes = folderNodes;

    const containerRef = React.useRef<HTMLDivElement | null>(null);

    const rowVirtualizer = useVirtualizer({
      count: renderedNodes.length,
      getScrollElement: () => containerRef.current,
      estimateSize: () => 29,
      overscan: 10,
    });

    const totalHeight = rowVirtualizer.getTotalSize();
    const items = rowVirtualizer.getVirtualItems();

    React.useLayoutEffect(() => {
      if (renderedNodes.length === 1) {
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
          smoothScroll: true,
        });
      }
      // Only scroll if the rootNodes changes or the selected node changes
      // otherwise opening/closing nodes will cause us to scroll again because the index changes
      // if we toggle a node above the selected node
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedNode, rootNodes, rowVirtualizer]);

    React.useLayoutEffect(() => {
      // Fix a weird issue where the sidebar doesn't measure the full height.
      const id = setInterval(rowVirtualizer.measure, 1000);
      return () => clearInterval(id);
    }, [rowVirtualizer.measure]);

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
        </div>
        <div>
          <Container
            ref={containerRef}
            onKeyDown={(e) => {
              let nextIndex = 0;
              if (e.code === 'ArrowDown' || e.code === 'ArrowUp') {
                nextIndex = indexOfLastSelectedNodeRef.current + (e.code === 'ArrowDown' ? 1 : -1);
                indexOfLastSelectedNodeRef.current = nextIndex;
                e.preventDefault();
                const nextNode =
                  renderedNodes[(nextIndex + renderedNodes.length) % renderedNodes.length]!;
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
                      <AssetSidebarNode
                        isOpen={openNodes.has(nodePathKey(node))}
                        fullAssetGraphData={fullAssetGraphData}
                        node={row}
                        level={node.level}
                        isSelected={
                          selectedNode?.id === node.id || selectedNodes.includes(row as GraphNode)
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
