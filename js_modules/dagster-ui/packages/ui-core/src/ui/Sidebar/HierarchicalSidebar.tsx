import {Box, Container, IconName, Inner, Row, Skeleton} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import invariant from 'invariant';
import * as React from 'react';

import {HierarchicalNode} from './HierarchicalNode';
import {HierarchyNode, TreeNode} from './types';
import {useQueryAndLocalStoragePersistedState} from '../../hooks/useQueryAndLocalStoragePersistedState';

const COLLATOR = new Intl.Collator(navigator.language, {sensitivity: 'base', numeric: true});

export function buildHierarchyFromPaths(paths: string[], includeFiles: boolean): HierarchyNode[] {
  // Note: This is a clever use of reduce that traverses down, upserting
  // nested objects for each layer of folders in the paths.
  const tree: TreeNode = {};
  paths.forEach((path) => {
    path.split('/').reduce((node, segment) => {
      node[segment] ||= {};
      return node[segment];
    }, tree);
  });

  const convert = (obj: TreeNode, prefix = ''): HierarchyNode[] =>
    Object.entries(obj)
      .map(([name, nodeValue]) => {
        const path = prefix ? `${prefix}/${name}` : name;
        if (Object.keys(nodeValue).length === 0) {
          return {type: 'file' as const, name, path};
        } else {
          return {type: 'folder' as const, name, path, children: convert(nodeValue, path)};
        }
      })
      .filter((t) => t.type === 'folder' || includeFiles)
      .sort((a, b) =>
        a.type !== b.type ? (a.type === 'folder' ? -1 : 1) : COLLATOR.compare(a.name, b.name),
      );

  return convert(tree);
}

export const HierarchicalSidebar = React.memo(
  ({
    hierarchyData,
    selectedPaths,
    onSelectPath,
    loading,
  }: {
    hierarchyData: HierarchyNode[];
    selectedPaths: string[];
    onSelectPath: (e: React.MouseEvent<any> | React.KeyboardEvent<any>, path: string) => void;
    loading: boolean;
  }) => {
    const lastSelectedPath = selectedPaths[selectedPaths.length - 1];

    const [openNodes, setOpenNodes] = useQueryAndLocalStoragePersistedState<Set<string>>({
      localStorageKey: 'hierarchy-sidebar-open-nodes',
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

    const [selectedPath, setSelectedPath] = React.useState<string | null>(null);

    const renderedNodes = React.useMemo(() => {
      return buildRenderedNodes(hierarchyData, openNodes);
    }, [hierarchyData, openNodes]);

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
      if (selectedPath) {
        // Auto-expand parent folders when a node is selected
        const selectedNodeIndex = renderedNodes.findIndex((node) => node.path === selectedPath);
        if (selectedNodeIndex >= 0) {
          const selectedRenderedNode = renderedNodes[selectedNodeIndex];
          if (selectedRenderedNode) {
            setOpenNodes((prevOpenNodes) => {
              const nextOpenNodes = new Set(prevOpenNodes);
              // Open all parent folders in the path
              const pathParts = selectedRenderedNode.path.split('/');
              for (let i = 1; i < pathParts.length; i++) {
                const parentPath = pathParts.slice(0, i).join('/');
                nextOpenNodes.add(parentPath);
              }
              return nextOpenNodes;
            });
          }
        }
        setSelectedPath(null);
      }
    }, [selectedPath, renderedNodes, setOpenNodes]);

    const indexOfLastSelectedNode = React.useMemo(() => {
      if (!lastSelectedPath) {
        return -1;
      }
      return renderedNodes.findIndex((node) => node.path === lastSelectedPath);
    }, [renderedNodes, lastSelectedPath]);

    const indexOfLastSelectedNodeRef = React.useRef(indexOfLastSelectedNode);
    indexOfLastSelectedNodeRef.current = indexOfLastSelectedNode;

    React.useLayoutEffect(() => {
      if (indexOfLastSelectedNode !== -1) {
        rowVirtualizer.scrollToIndex(indexOfLastSelectedNode, {
          align: 'center',
          behavior: 'smooth',
        });
      }
      // Only scroll if the selected node changes
      // otherwise opening/closing nodes will cause us to scroll again because the index changes
      // if we toggle a node above the selected node
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [indexOfLastSelectedNode, rowVirtualizer]);

    return (
      <div style={{height: '100%'}}>
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
            style={{padding: 12, paddingLeft: 0}}
            onKeyDown={(e) => {
              let nextIndex = 0;
              if (e.code === 'ArrowDown' || e.code === 'ArrowUp') {
                nextIndex = indexOfLastSelectedNodeRef.current + (e.code === 'ArrowDown' ? 1 : -1);
                indexOfLastSelectedNodeRef.current = nextIndex;
                e.preventDefault();
                const nextNode =
                  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                  renderedNodes[(nextIndex + renderedNodes.length) % renderedNodes.length]!;
                setSelectedPath(nextNode.path);
                onSelectPath(e, nextNode.path);
              } else if (e.code === 'ArrowLeft' || e.code === 'ArrowRight') {
                const open = e.code === 'ArrowRight';
                const node = renderedNodes[indexOfLastSelectedNode];
                if (!node || node.type !== 'folder') {
                  return;
                }
                setOpenNodes((nodes) => {
                  const openNodes = new Set(nodes);
                  if (open) {
                    openNodes.add(node.path);
                  } else {
                    openNodes.delete(node.path);
                  }
                  return openNodes;
                });
              }
            }}
          >
            <Inner $totalHeight={totalHeight}>
              {items.map(({index, key, size, start}) => {
                const node = renderedNodes[index];
                invariant(node, 'Sidebar node is required');

                const isSelected = selectedPaths.includes(node.path);
                const isLastSelected = lastSelectedPath === node.path;
                const isOpen = openNodes.has(node.path);

                return (
                  <Row $height={size} $start={start} key={key}>
                    <div data-index={index} ref={rowVirtualizer.measureElement}>
                      <HierarchicalNode
                        node={node}
                        isOpen={isOpen}
                        isSelected={isSelected}
                        isLastSelected={isLastSelected}
                        onToggleOpen={() => {
                          if (node.type === 'folder') {
                            setOpenNodes((nodes) => {
                              const openNodes = new Set(nodes);
                              if (isOpen) {
                                openNodes.delete(node.path);
                              } else {
                                openNodes.add(node.path);
                              }
                              return openNodes;
                            });
                          }
                        }}
                        onSelect={(e) => {
                          setSelectedPath(node.path);
                          onSelectPath(e, node.path);
                        }}
                      />
                    </div>
                  </Row>
                );
              })}
            </Inner>
          </Container>
        )}
      </div>
    );
  },
);

function buildRenderedNodes(
  hierarchyData: HierarchyNode[],
  openNodes: Set<string>,
): RenderedNode[] {
  const flattenedNodes: RenderedNode[] = [];

  function traverse(nodes: HierarchyNode[], level: number, pathPrefix: string = '') {
    const sortedNodes = [...nodes].sort((a, b) => {
      if (a.type !== b.type) {
        return a.type === 'folder' ? -1 : 1; // Folders first, then files
      }
      return COLLATOR.compare(a.name, b.name);
    });

    for (const node of sortedNodes) {
      const currentPath = pathPrefix ? `${pathPrefix}/${node.name}` : node.name;

      flattenedNodes.push({
        level,
        name: node.name,
        path: currentPath,
        type: node.type,
        icon: node.icon || (node.type === 'folder' ? 'folder_open' : 'asset'),
        hasChildren: node.type === 'folder' && 'children' in node && node.children.length > 0,
      });

      if (node.type === 'folder' && 'children' in node && openNodes.has(currentPath)) {
        traverse(node.children, level + 1, currentPath);
      }
    }
  }

  traverse(hierarchyData, 1);
  return flattenedNodes;
}
