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
  TextInput,
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

export const AssetGraphExplorerSidebar = React.memo(
  ({
    assetGraphData,
    lastSelectedNode,
    selectNode,
  }: {
    assetGraphData: GraphData;
    lastSelectedNode: GraphNode;
    selectNode: (e: React.MouseEvent<any>, nodeId: string) => void;
  }) => {
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
          // Exclude nodes without data, these are nodes from another group which we don't have graph data for,
          // We don't want those nodes to show up as roots in the sidebar
          .filter(
            (nodeId) =>
              Object.keys(assetGraphData.upstream[nodeId] || {}).filter(
                (id) => !!assetGraphData.nodes[id],
              ).length === 0,
          )
          .sort((nodeA, nodeB) => COLLATOR.compare(nodeA, nodeB));
      });
      return {rootGroupsWithRootNodes: groups, nodeToGroupId};
    }, [assetGraphData]);

    const [openNodes, setOpenNodes] = React.useState<Set<string>>(() => {
      const set = new Set<string>();
      if (Object.keys(rootGroupsWithRootNodes).length === 1) {
        set.add(Object.keys(rootGroupsWithRootNodes)[0]!);
      }
      return set;
    });

    const renderedNodes = React.useMemo(() => {
      const queue = Object.entries(rootGroupsWithRootNodes).map(([_, {id}]) => ({level: 1, id}));

      const renderedNodes: {level: number; id: string}[] = [];
      while (queue.length) {
        const node = queue.shift()!;
        renderedNodes.push(node);
        if (openNodes.has(node.id)) {
          const groupNode = rootGroupsWithRootNodes[node.id];
          let downstream;
          if (groupNode) {
            downstream = groupNode.nodes;
          } else {
            downstream = Object.keys(assetGraphData.downstream[node.id] || {});
          }
          if (downstream) {
            queue.unshift(...downstream.map((id) => ({level: node.level + 1, id})));
          }
        }
      }
      return renderedNodes.filter(
        // Exclude nodes without data, these are nodes from another group which we don't have graph data for,
        // We don't want those nodes to show up as leaf nodes in the sidebar
        ({id}) => !!assetGraphData.nodes[id] || !!rootGroupsWithRootNodes[id],
      );
    }, [assetGraphData, openNodes, rootGroupsWithRootNodes]);

    const containerRef = React.useRef<HTMLDivElement | null>(null);
    const {containerProps, viewport} = useViewport();

    const rowVirtualizer = useVirtualizer({
      count: renderedNodes.length,
      getScrollElement: () => containerRef.current,
      estimateSize: () => 34,

      // TODO: Figure out why virtualizer isn't filling up all of the space automatically...
      overscan: viewport.height / 34,
    });

    const totalHeight = rowVirtualizer.getTotalSize();
    const items = rowVirtualizer.getVirtualItems();

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

    return (
      <Box flex={{direction: 'column'}} style={{height: '100%'}}>
        <Box flex={{direction: 'column'}} padding={8}>
          <SearchContainer>
            <Box flex={{direction: 'row', gap: 4}}>
              <Icon name="search" color={Colors.Gray200} size={20} />
              <Box flex={{direction: 'column', grow: 1}}>
                <SearchInput />
              </Box>
            </Box>
          </SearchContainer>
        </Box>
        <Box flex={{grow: 1}}>
          <Container
            style={{width: '100%'}}
            {...containerProps}
            ref={(el) => {
              if (el) {
                console.log({el});
                containerProps.ref(el);
                containerRef.current = el;
              }
            }}
          >
            <Inner $totalHeight={totalHeight}>
              {items.map(({index, key, size, start, measureElement}) => {
                const node = renderedNodes[index]!;
                const row = assetGraphData.nodes[node.id] ?? rootGroupsWithRootNodes[node.id];
                setTimeout(measureElement, 100);
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
                        isOpen={openNodes.has(node.id)}
                        assetGraphData={assetGraphData}
                        node={row}
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
                    ) : null}
                  </Row>
                );
              })}
            </Inner>
          </Container>
        </Box>
      </Box>
    );
  },
);

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

  const upstream = isGroupNode
    ? []
    : Object.keys(assetGraphData.upstream[node.id] ?? {}).filter(
        (id) => !!assetGraphData.nodes[id],
      );
  const downstream = isGroupNode
    ? node.nodes
    : Object.keys(assetGraphData.downstream[node.id] ?? {}).filter(
        (id) => !!assetGraphData.nodes[id],
      );
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
      style={{
        ...(downstream && !isGroupNode ? {cursor: 'pointer'} : {}),
      }}
    >
      <BoxWrapper level={level}>
        <Box padding={{right: 12}} flex={{direction: 'row', gap: 2, alignItems: 'center'}}>
          {downstream.length ? (
            <div
              onClick={(e) => {
                e.stopPropagation();
                toggleOpen();
              }}
              style={{cursor: 'pointer'}}
            >
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
            padding={{horizontal: 12, vertical: 8}}
            style={{borderRadius: '8px', ...(isSelected ? {background: Colors.Gray100} : {})}}
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
              assets={downstream}
              assetGraphData={assetGraphData}
              isOpen={showDownstream}
              close={() => {
                setShowDownstream(false);
              }}
              selectNode={selectNode}
            />
            <UpstreamDownstreamDialog
              title="Upstream assets"
              assets={upstream}
              assetGraphData={assetGraphData}
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
              placement="right"
              shouldReturnFocusOnClose
            >
              <div style={{cursor: 'pointer'}}>
                <Icon name="expand_more" color={Colors.Gray500} />
              </div>
            </Popover>
          </Box>
        </Box>
      </BoxWrapper>
    </Box>
  );
};

const UpstreamDownstreamDialog = ({
  title,
  assets,
  assetGraphData,
  isOpen,
  close,
  selectNode,
}: {
  title: string;
  assets: string[];
  assetGraphData: GraphData;
  isOpen: boolean;
  close: () => void;
  selectNode: (e: React.MouseEvent<any>, nodeId: string) => void;
}) => {
  return (
    <Dialog isOpen={isOpen} onClose={close} title={title}>
      <DialogBody>
        {assets.map((assetId) => {
          const asset = assetGraphData.nodes[assetId];
          if (!asset) {
            return null;
          }
          return (
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
          );
        })}
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

const BoxWrapper = ({level, children}: {level: number; children: React.ReactNode}) => {
  const wrapper = React.useMemo(() => {
    let sofar = children;
    for (let i = 0; i < level; i++) {
      sofar = (
        <Box padding={{left: 12}} border={{side: 'left', width: 1, color: Colors.KeylineGray}}>
          {sofar}
        </Box>
      );
    }
    return sofar;
  }, [level, children]);

  return <>{wrapper}</>;
};

const SearchInput = styled.input`
  border: none;
  color: ${Colors.Gray600};
  font-size: 18px;
  margin-left: 4px;
  outline: none;
  width: 100%;

  &::placeholder {
    color: ${Colors.Gray200};
  }
`;

const SearchContainer = styled.div`
  background-color: ${Colors.White};
  border-radius: 4px;
  box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.1);
`;
