import {
  Box,
  Button,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Icon,
  Menu,
  MenuItem,
  Popover,
  useViewport,
  UnstyledButton,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React from 'react';
import styled from 'styled-components';

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

const indentColors = [
  Colors.Blue100,
  Colors.LightPurple,
  Colors.Yellow200,
  Colors.Gray300,
  Colors.KeylineGray,
];

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
  }, [lastSelectedNode, nodeToGroupId[lastSelectedNode?.id ?? 0]]);

  const {containerProps, viewport} = useViewport();

  React.useLayoutEffect(() => {
    rowVirtualizer.measure();
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
                toggleOpen={() => {
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
                selectNode={selectNode}
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
  selectNode,
  isOpen,
  measureElement,
  isSelected,
}: {
  assetGraphData: GraphData;
  node: GraphNode | GroupNode;
  level: number;
  toggleOpen: () => void;
  selectNode: (e: React.MouseEvent, nodeId: string) => void;
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
    setTimeout(() => {
      if (elementRef.current) {
        measureElement(elementRef.current);
      }
    }, 100);
  }, [measureElement, isOpen]);

  const [showDownstream, setShowDownstream] = React.useState(false);
  const [showUpstream, setShowUpstream] = React.useState(false);

  return (
    <Box
      ref={elementRef}
      onClick={(e) => selectNode(e, node.id)}
      border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      style={{
        ...(downstream && !isGroupNode ? {cursor: 'pointer'} : {}),
        ...(isSelected ? {background: Colors.LightPurple} : {}),
      }}
      padding={{left: (8 * level) as any, right: 24}}
    >
      <Box
        padding={{vertical: 8, left: (downstream.length ? 0 : 20) as any}}
        border={{side: 'left', width: 1, color: indentColors[level % indentColors.length]!}}
        flex={{direction: 'row', gap: 4, alignItems: 'center'}}
      >
        {downstream.length ? (
          <div onClick={toggleOpen} style={{cursor: 'pointer'}}>
            <Icon
              name="arrow_drop_down"
              style={{transform: isOpen ? 'rotate(0deg)' : 'rotate(-90deg)'}}
            />
          </div>
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
          <UpstreamDownstreamDialog
            title="Downstream assets"
            assets={downstream.map((id) => assetGraphData.nodes[id]!)}
            isOpen={showDownstream}
            close={() => {
              setShowDownstream(false);
            }}
            selectNode={selectNode}
          />
          <UpstreamDownstreamDialog
            title="Upstream assets"
            assets={upstream.map((id) => assetGraphData.nodes[id]!)}
            isOpen={showUpstream}
            close={() => {
              setShowUpstream(false);
            }}
            selectNode={selectNode}
          />
          <Popover
            content={
              <Menu>
                {upstream.length ? (
                  <MenuItem
                    text={`View upstream (${upstream.length})`}
                    onClick={() => {
                      setShowUpstream(true);
                    }}
                  />
                ) : null}
                {downstream.length ? (
                  <MenuItem
                    text={`View downstream (${downstream.length})`}
                    onClick={() => {
                      setShowDownstream(true);
                    }}
                  />
                ) : null}
              </Menu>
            }
            hoverOpenDelay={100}
            hoverCloseDelay={100}
            placement="top"
            shouldReturnFocusOnClose
          >
            <div style={{cursor: 'pointer'}}>
              <Icon name="more_horiz" />
            </div>
          </Popover>
        </Box>
      </Box>
    </Box>
  );
};

const UpstreamDownstreamDialog = ({
  title,
  assets,
  isOpen,
  close,
  selectNode,
}: {
  title: string;
  assets: GraphNode[];
  isOpen: boolean;
  close: () => void;
  selectNode: (e: React.MouseEvent<any>, nodeId: string) => void;
}) => {
  return (
    <Dialog isOpen={isOpen} onClose={close} title={title}>
      <DialogBody>
        {assets.map((asset) => (
          <UnstyledButton
            key={asset.id}
            onClick={(e) => {
              selectNode(e, asset.id);
              close();
            }}
          >
            <DialogAssetButton padding={{vertical: 8, horizontal: 12}}>
              {asset.assetKey.path[asset.assetKey.path.length - 1]}
            </DialogAssetButton>
          </UnstyledButton>
        ))}
      </DialogBody>
      <DialogFooter topBorder>
        <Button onClick={close} intent="primary">
          Close
        </Button>
      </DialogFooter>
    </Dialog>
  );
};

const DialogAssetButton = styled(Box)`
  border-radius: 8px;
  &:hover {
    background: ${Colors.Gray100};
  }
`;
