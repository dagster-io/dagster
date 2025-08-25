import {Box, Skeleton} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';

import {AssetSidebarNode} from './AssetSidebarNode';
import {FolderNodeType, TreeNodeType, nodePathKey} from './util';
import {ExplorerPath} from '../../pipelines/PipelinePathUtils';
import {Container, Inner, Row} from '../../ui/VirtualizedTable';
import {AssetGroup} from '../AssetGraphExplorer';
import {GraphData, GraphNode} from '../Utils';

export interface AssetSidebarListViewProps {
  loading: boolean;
  renderedNodes: TreeNodeType[] | FolderNodeType[];
  graphData: GraphData;
  fullAssetGraphData: GraphData;
  selectedNodes: GraphNode[];
  selectedNode: null | {id: string; path: string} | {id: string};
  lastSelectedNode: GraphNode | undefined;
  openNodes: Set<string>;
  setOpenNodes: React.Dispatch<React.SetStateAction<Set<string>>>;
  setSelectedNode: React.Dispatch<
    React.SetStateAction<null | {id: string; path: string} | {id: string}>
  >;
  selectNode: (e: React.MouseEvent<any> | React.KeyboardEvent<any>, nodeId: string) => void;
  explorerPath: ExplorerPath;
  onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
  onFilterToGroup: (group: AssetGroup) => void;
  viewType: 'tree' | 'group';
  direction?: 'root-to-leaf' | 'leaf-to-root';
  collapseAllNodes?: () => void;
}

export const AssetSidebarListView = ({
  loading,
  renderedNodes,
  graphData,
  fullAssetGraphData,
  selectedNodes,
  selectedNode,
  lastSelectedNode,
  openNodes,
  setOpenNodes,
  setSelectedNode,
  selectNode,
  collapseAllNodes,
  explorerPath,
  onChangeExplorerPath,
  onFilterToGroup,

  viewType,
  // Direction is only used when viewType is 'tree'
  direction = 'root-to-leaf',
}: AssetSidebarListViewProps) => {
  const containerRef = React.useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: renderedNodes.length,
    getScrollElement: () => containerRef.current,
    estimateSize: () => 32,
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  const indexOfLastSelectedNode = React.useMemo(() => {
    if (!selectedNode) {
      return -1;
    }
    if (viewType === 'tree') {
      return 'path' in selectedNode
        ? renderedNodes.findIndex((node) => 'path' in node && node.path === selectedNode.path)
        : -1;
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
  }, [renderedNodes, selectedNode, viewType]);

  const indexOfLastSelectedNodeRef = React.useRef(indexOfLastSelectedNode);
  indexOfLastSelectedNodeRef.current = indexOfLastSelectedNode;

  React.useEffect(() => {
    if (indexOfLastSelectedNode !== -1) {
      rowVirtualizer.scrollToIndex(indexOfLastSelectedNode, {
        align: 'center',
        behavior: 'smooth',
      });
    }
  }, [selectedNode, rowVirtualizer, indexOfLastSelectedNode]);

  if (loading) {
    return (
      <Box flex={{direction: 'column', gap: 9}} padding={12}>
        <Skeleton $height={21} $width="50%" />
        <Skeleton $height={21} $width="80%" />
        <Skeleton $height={21} $width="65%" />
        <Skeleton $height={21} $width="90%" />
      </Box>
    );
  }

  return (
    <Container
      ref={containerRef}
      onKeyDown={(e) => {
        let nextIndex = 0;
        if (e.code === 'ArrowDown' || e.code === 'ArrowUp') {
          nextIndex = indexOfLastSelectedNodeRef.current + (e.code === 'ArrowDown' ? 1 : -1);
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
      <Inner $totalHeight={totalHeight}>
        {items.map(({index, key, size, start}) => {
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          const node = renderedNodes[index]!;
          const isCodeLocationNode = 'locationName' in node;
          const isGroupNode = 'groupNode' in node;
          const row = !isCodeLocationNode && !isGroupNode ? graphData.nodes[node.id] : node;
          const isSelected =
            selectedNode?.id === node.id || selectedNodes.includes(row as GraphNode);
          return (
            <Row $height={size} $start={start} key={key}>
              <div data-index={index} ref={rowVirtualizer.measureElement}>
                <AssetSidebarNode
                  isOpen={openNodes.has(nodePathKey(node))}
                  fullAssetGraphData={fullAssetGraphData}
                  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
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
                  collapseAllNodes={collapseAllNodes}
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
                  graphData={graphData}
                  viewType={viewType}
                  direction={direction}
                />
              </div>
            </Row>
          );
        })}
      </Inner>
    </Container>
  );
};
