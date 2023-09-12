import {Box, ButtonLink, Colors, Icon, useViewport} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React from 'react';

import {withMiddleTruncation} from '../app/Util';
import {Container, Inner, Row} from '../ui/VirtualizedTable';

import {NameTooltipStyle} from './AssetNode';
import {GraphData, GraphNode} from './Utils';

const COLLATOR = new Intl.Collator(navigator.language, {sensitivity: 'base', numeric: true});

type GroupNode = {
  nodes: string[];
  groupName: string | null;
  repositoryLocationName: string;
  repositoryName: string;
  id: string;
};

export const AssetGraphExplorerSidebar = ({
  assetGraphData,
  lastSelectedNode,
  selectNode,
}: {
  assetGraphData: GraphData;
  lastSelectedNode: GraphNode;
  selectNode: (e: React.MouseEvent<any>, nodeId: string) => void;
}) => {
  const [openNodes, setOpenNodes] = React.useState<Set<string>>(() => new Set());
  const {rootGroupsWithRootNodes, nodeToGroupId} = React.useMemo(() => {
    const nodeToGroupId: Record<string, string> = {};
    const groups: Record<string, GroupNode> = {};
    Object.entries(assetGraphData.nodes).forEach(([_, node]) => {
      const groupName = node.definition.groupName;
      const repositoryLocationName = node.definition.repository.location.name;
      const repositoryName = node.definition.repository.name;
      const groupId = `${groupName}@${repositoryName}@${repositoryLocationName}`;
      groups[groupId] = groups[groupId] || {
        nodes: [],
        groupName,
        repositoryLocationName,
        repositoryName,
        id: groupId,
      };
      groups[groupId]!.nodes.push(node.id);
      nodeToGroupId[node.id] = groupId;
    });
    Object.entries(groups).forEach(([_, group]) => {
      group.nodes = group.nodes
        .filter((nodeId) => !assetGraphData.upstream[nodeId])
        .sort((nodeA, nodeB) => COLLATOR.compare(nodeA, nodeB));
    });
    return {rootGroupsWithRootNodes: groups, nodeToGroupId};
  }, [assetGraphData]);

  const renderedNodes = React.useMemo(() => {
    const queue = Object.entries(rootGroupsWithRootNodes).map(([_, {id}]) => ({level: 1, id}));

    const renderedNodes: {level: number; id: string}[] = [];
    while (queue.length) {
      const node = queue.shift()!;
      renderedNodes.push(node);
      if (openNodes.has(node.id)) {
        const groupNode = rootGroupsWithRootNodes[node.id];
        if (groupNode) {
          const downstream = groupNode.nodes;
          if (downstream.length) {
            queue.unshift(...downstream.map((id) => ({level: 2, id})));
          }
        } else {
          const downstream = assetGraphData.downstream[node.id];
          if (downstream) {
            queue.unshift(...Object.keys(downstream).map((id) => ({level: node.level + 1, id})));
          }
        }
      }
    }
    return renderedNodes;
  }, [assetGraphData.downstream, openNodes, rootGroupsWithRootNodes]);

  const containerRef = React.useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: renderedNodes.length,
    getScrollElement: () => containerRef.current,
    estimateSize: () => 32,
    overscan: 5,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  React.useLayoutEffect(() => {
    requestAnimationFrame(() => {
      rowVirtualizer.measure();
    });
  }, [rowVirtualizer]);

  const indexOfLastSelectedNode = React.useMemo(
    () =>
      lastSelectedNode ? renderedNodes.findIndex((node) => node.id === lastSelectedNode.id) : -1,
    [renderedNodes, lastSelectedNode],
  );

  React.useLayoutEffect(() => {
    if (indexOfLastSelectedNode !== -1) {
      rowVirtualizer.scrollToIndex(indexOfLastSelectedNode);
    }
  }, [indexOfLastSelectedNode, rowVirtualizer]);

  React.useEffect(() => {
    if (lastSelectedNode) {
      setOpenNodes((nodes) => {
        const nextOpenNodes = new Set(nodes);
        nextOpenNodes.add(lastSelectedNode.id);
        const upstreamQueue = Object.keys(assetGraphData.upstream[lastSelectedNode.id] ?? {});
        while (upstreamQueue.length) {
          const next = upstreamQueue.pop()!;
          const nextUpstream = Object.keys(assetGraphData.upstream[next] ?? {});
          upstreamQueue.push(...nextUpstream);
          nextOpenNodes.add(next);
        }
        nextOpenNodes.add(nodeToGroupId[lastSelectedNode.id]!);
        return nextOpenNodes;
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lastSelectedNode, nodeToGroupId]);

  const {containerProps, viewport} = useViewport();

  React.useLayoutEffect(() => {
    rowVirtualizer.measure();
    console.log('measuring');
  }, [viewport.width, viewport.height, rowVirtualizer]);

  return (
    <Container
      {...containerProps}
      ref={(el) => {
        if (el) {
          containerProps.ref(el);
          containerRef.current = el;
        }
      }}
    >
      <Inner $totalHeight={totalHeight}>
        {items.map(({index, key, size, start, measureElement}) => {
          const node = renderedNodes[index]!;
          return (
            <Row
              $height={size}
              $start={start}
              key={key}
              style={{overflow: 'visible'}}
              ref={measureElement}
            >
              <Node
                isOpen={openNodes.has(node.id)}
                assetGraphData={assetGraphData}
                node={(assetGraphData.nodes[node.id] ?? rootGroupsWithRootNodes[node.id])!}
                level={node.level}
                isSelected={lastSelectedNode?.id === node.id}
                toggleOpen={(e: React.MouseEvent) => {
                  selectNode(e, node.id);
                  setOpenNodes((nodes) => {
                    const openNodes = new Set(nodes);
                    const isOpen = openNodes.has(node.id);
                    if (isOpen) {
                      openNodes.delete(node.id);
                    } else {
                      openNodes.add(node.id);
                    }
                    return openNodes;
                  });
                }}
                measureElement={measureElement}
              />
            </Row>
          );
        })}
      </Inner>
    </Container>
  );
};

const Node = ({
  assetGraphData,
  node,
  level,
  toggleOpen,
  isOpen,
  measureElement,
  isSelected,
}: {
  assetGraphData: GraphData;
  node: GraphNode | GroupNode;
  level: number;
  toggleOpen: (e: React.MouseEvent) => void;
  isOpen: boolean;
  measureElement: (el: HTMLDivElement) => void;
  isSelected: boolean;
}) => {
  const isGroupNode = 'groupName' in node;

  const displayName = isGroupNode
    ? `${node.groupName ?? 'default'} in ${node.repositoryName}@${node.repositoryLocationName}`
    : node.assetKey.path[node.assetKey.path.length - 1]!;

  const upstream = isGroupNode ? [] : Object.keys(assetGraphData.upstream[node.id] ?? {});
  const downstream = isGroupNode
    ? node.nodes
    : Object.keys(assetGraphData.downstream[node.id] ?? {});
  const elementRef = React.useRef<HTMLDivElement | null>(null);
  React.useLayoutEffect(() => {
    if (elementRef.current) {
      measureElement(elementRef.current);
    }
  }, [measureElement, isOpen]);

  return (
    <Box
      ref={elementRef}
      onClick={toggleOpen}
      border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      style={{
        ...(downstream ? {cursor: 'pointer'} : {}),
        ...(isSelected ? {background: Colors.LightPurple} : {}),
      }}
      padding={{vertical: 8, left: (8 * level + (downstream.length ? 0 : 20)) as any, right: 24}}
      flex={{direction: 'row', gap: 4, alignItems: 'center'}}
    >
      {downstream.length ? (
        <Icon
          name="arrow_drop_down"
          style={{transform: isOpen ? 'rotate(0deg)' : 'rotate(-90deg)'}}
        />
      ) : null}
      <Box
        flex={{
          direction: 'row',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
          grow: 1,
        }}
      >
        <div
          data-tooltip={displayName}
          data-tooltip-style={NameTooltipStyle}
          style={{overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}
        >
          {withMiddleTruncation(displayName, {maxLength: 30})}
        </div>
        {upstream.length > 1 ? <ButtonLink>{upstream.length}</ButtonLink> : null}
      </Box>
    </Box>
  );
};
