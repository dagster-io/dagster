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
  TextInput,
  MiddleTruncate,
  useViewport,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React from 'react';
import styled from 'styled-components';

import {Container, Inner, Row} from '../ui/VirtualizedTable';

import {GraphData, GraphNode} from './Utils';

const COLLATOR = new Intl.Collator(navigator.language, {sensitivity: 'base', numeric: true});

export const AssetGraphExplorerSidebar = React.memo(
  ({
    assetGraphData,
    lastSelectedNode,
    selectNode,
  }: {
    assetGraphData: GraphData;
    lastSelectedNode: GraphNode;
    selectNode: (e: React.MouseEvent<any> | React.KeyboardEvent<any>, nodeId: string) => void;
  }) => {
    const [openNodes, setOpenNodes] = React.useState<Set<string>>(new Set());
    const [selectedNode, setSelectedNode] = React.useState<null | {id: string; path: string}>(null);

    const rootNodes = React.useMemo(
      () =>
        Object.keys(assetGraphData.nodes)
          .filter((id) => !assetGraphData.upstream[id])
          .sort((a, b) =>
            COLLATOR.compare(
              getDisplayName(assetGraphData.nodes[a]!),
              getDisplayName(assetGraphData.nodes[b]!),
            ),
          ),
      [assetGraphData],
    );

    const renderedNodes = React.useMemo(() => {
      const queue = rootNodes.map((id) => ({level: 1, id, path: id}));

      const renderedNodes: {level: number; id: string; path: string}[] = [];
      while (queue.length) {
        const node = queue.shift()!;
        renderedNodes.push(node);
        if (openNodes.has(node.path)) {
          const downstream = Object.keys(assetGraphData.downstream[node.id] || {});
          if (downstream) {
            queue.unshift(
              ...downstream
                .filter((id) => assetGraphData.nodes[id])
                .map((id) => ({level: node.level + 1, id, path: `${node.path}:${id}`})),
            );
          }
        }
      }
      return renderedNodes;
    }, [assetGraphData.downstream, assetGraphData.nodes, openNodes, rootNodes]);

    const containerRef = React.useRef<HTMLDivElement | null>(null);

    const rowVirtualizer = useVirtualizer({
      count: renderedNodes.length,
      getScrollElement: () => containerRef.current,
      estimateSize: () => 38,
      overscan: 10,
    });

    const totalHeight = rowVirtualizer.getTotalSize();
    const items = rowVirtualizer.getVirtualItems();

    React.useLayoutEffect(() => {
      if (lastSelectedNode && lastSelectedNode.id !== selectedNode?.id) {
        setOpenNodes((prevOpenNodes) => {
          let path = lastSelectedNode.id;
          let currentId = lastSelectedNode.id;
          let next: string | undefined;
          while ((next = Object.keys(assetGraphData.upstream[currentId] ?? {})[0])) {
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
          setSelectedNode({id: lastSelectedNode.id, path: currentPath});
          return nextOpenNodes;
        });
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [lastSelectedNode]);

    const indexOfLastSelectedNode = React.useMemo(
      () =>
        selectedNode?.path
          ? renderedNodes.findIndex((node) => node.path === selectedNode?.path)
          : -1,
      // eslint-disable-next-line react-hooks/exhaustive-deps
      [renderedNodes, selectedNode?.path],
    );

    React.useLayoutEffect(() => {
      if (indexOfLastSelectedNode !== -1) {
        rowVirtualizer.scrollToIndex(indexOfLastSelectedNode);
      }
    }, [indexOfLastSelectedNode, rowVirtualizer]);

    return (
      <div style={{display: 'grid', gridTemplateRows: 'auto minmax(0, 1fr)', height: '100%'}}>
        <Box flex={{direction: 'column'}} padding={8}>
          <SearchFilter
            values={React.useMemo(() => {
              return Object.entries(assetGraphData.nodes).map(([id, node]) => ({
                value: id,
                label: getDisplayName(node),
              }));
            }, [assetGraphData.nodes])}
            onSelectValue={selectNode}
          />
        </Box>
        <div>
          <Container ref={containerRef}>
            <Inner $totalHeight={totalHeight}>
              {items.map(({index, key, size, start, measureElement}) => {
                const node = renderedNodes[index]!;
                const row = assetGraphData.nodes[node.id];
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
                        isSelected={selectedNode?.path === node.path}
                        toggleOpen={() => {
                          setSelectedNode(node);
                          setOpenNodes((nodes) => {
                            const openNodes = new Set(nodes);
                            const isOpen = openNodes.has(node.path);
                            if (isOpen) {
                              openNodes.delete(node.path);
                            } else {
                              openNodes.add(node.path);
                            }
                            return openNodes;
                          });
                        }}
                        selectNode={(e, id) => {
                          selectNode(e, id);
                        }}
                        selectThisNode={(e) => {
                          selectNode(e, node.id);
                          setSelectedNode(node);
                        }}
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

const Node = ({
  assetGraphData,
  node,
  level,
  toggleOpen,
  selectNode,
  isOpen,
  isSelected,
  selectThisNode,
}: {
  assetGraphData: GraphData;
  node: GraphNode;
  level: number;
  toggleOpen: () => void;
  selectThisNode: (e: React.MouseEvent<any> | React.KeyboardEvent<any>) => void;
  selectNode: (e: React.MouseEvent<any> | React.KeyboardEvent<any>, nodeId: string) => void;
  isOpen: boolean;
  isSelected: boolean;
}) => {
  const displayName = getDisplayName(node);

  const upstream = Object.keys(assetGraphData.upstream[node.id] ?? {}).filter(
    (id) => !!assetGraphData.nodes[id],
  );
  const downstream = Object.keys(assetGraphData.downstream[node.id] ?? {}).filter(
    (id) => !!assetGraphData.nodes[id],
  );
  const elementRef = React.useRef<HTMLDivElement | null>(null);

  const [showDownstream, setShowDownstream] = React.useState(false);
  const [showUpstream, setShowUpstream] = React.useState(false);

  return (
    <>
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
      <Box ref={elementRef} onClick={selectThisNode}>
        <BoxWrapper level={level}>
          <Box
            padding={{right: 12, vertical: 2}}
            flex={{direction: 'row', gap: 2, alignItems: 'center'}}
          >
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
            <GrayOnHoverBox
              flex={{
                direction: 'row',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 12,
                grow: 1,
                shrink: 1,
              }}
              padding={{horizontal: 12, vertical: 8}}
              style={{
                width: '100%',
                borderRadius: '8px',
                ...(isSelected ? {background: Colors.LightPurple} : {}),
              }}
            >
              <MiddleTruncate text={displayName} />
              {upstream.length || downstream.length ? (
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
                  <ExpandMore style={{cursor: 'pointer'}}>
                    <Icon name="expand_more" color={Colors.Gray500} />
                  </ExpandMore>
                </Popover>
              ) : null}
            </GrayOnHoverBox>
          </Box>
        </BoxWrapper>
      </Box>
    </>
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
  selectNode: (e: React.MouseEvent<any> | React.KeyboardEvent<any>, nodeId: string) => void;
}) => {
  return (
    <Dialog isOpen={isOpen} onClose={close} title={title}>
      <DialogBody>
        <Menu>
          {assets.map((assetId) => {
            const asset = assetGraphData.nodes[assetId];
            if (!asset) {
              return null;
            }
            return (
              <MenuItem
                text={asset.assetKey.path[asset.assetKey.path.length - 1]}
                key={asset.id}
                onClick={(e) => {
                  selectNode(e, asset.id);
                  close();
                }}
              />
            );
          })}
        </Menu>
      </DialogBody>
      <DialogFooter topBorder>
        <Button onClick={close} intent="primary">
          Close
        </Button>
      </DialogFooter>
    </Dialog>
  );
};

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

function getDisplayName(node: GraphNode) {
  return node.assetKey.path[node.assetKey.path.length - 1]!;
}

const SearchFilter = <T,>({
  values,
  onSelectValue,
}: {
  values: {label: string; value: T}[];
  onSelectValue: (e: React.MouseEvent<any>, value: T) => void;
}) => {
  const [searchValue, setSearchValue] = React.useState('');
  const filteredValues = React.useMemo(() => {
    if (searchValue) {
      return values.filter(({label}) => label.toLowerCase().includes(searchValue.toLowerCase()));
    }
    return values;
  }, [searchValue, values]);

  const {viewport, containerProps} = useViewport();
  return (
    <Popover
      placement="bottom-start"
      targetTagName="div"
      content={
        searchValue ? (
          <Box
            style={{
              width: viewport.width + 'px',
              borderRadius: '8px',
              maxHeight: 'min(500px, 50vw)',
              overflow: 'auto',
            }}
          >
            <Menu>
              {filteredValues.length ? (
                filteredValues.map((value) => (
                  <MenuItem
                    key={value.label}
                    onClick={(e) => {
                      onSelectValue(e, value.value);
                      setSearchValue('');
                    }}
                    text={value.label}
                  />
                ))
              ) : (
                <Box padding={8}>No results</Box>
              )}
            </Menu>
          </Box>
        ) : (
          <div />
        )
      }
    >
      <div style={{display: 'grid', gridTemplateColumns: '1fr'}}>
        <TextInput
          icon="search"
          value={searchValue}
          onChange={(e) => {
            setSearchValue(e.target.value);
          }}
          placeholder="Search assets"
          {...(containerProps as any)}
        />
      </div>
    </Popover>
  );
};

const ExpandMore = styled.div``;

const GrayOnHoverBox = styled(Box)`
  border-radius: 8px;
  &:hover {
    background: ${Colors.Gray100};
    transition: background 100ms linear;
    ${ExpandMore} {
      visibility: visible;
    }
  }
  ${ExpandMore} {
    visibility: hidden;
  }
`;
