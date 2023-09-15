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

import {AssetKey} from '../assets/types';
import {ExplorerPath} from '../pipelines/PipelinePathUtils';
import {Container, Inner, Row} from '../ui/VirtualizedTable';

import {GraphData, GraphNode} from './Utils';

const COLLATOR = new Intl.Collator(navigator.language, {sensitivity: 'base', numeric: true});

export const AssetGraphExplorerSidebar = React.memo(
  ({
    assetGraphData,
    lastSelectedNode,
    selectNode: _selectNode,
    explorerPath,
    onChangeExplorerPath,
    allAssetKeys,
  }: {
    assetGraphData: GraphData;
    lastSelectedNode: GraphNode;
    selectNode: (e: React.MouseEvent<any> | React.KeyboardEvent<any>, nodeId: string) => void;
    explorerPath: ExplorerPath;
    onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
    allAssetKeys: AssetKey[];
  }) => {
    const selectNode: typeof _selectNode = (e, id) => {
      _selectNode(e, id);
      if (!assetGraphData.nodes[id]) {
        const path = JSON.parse(id);
        const nextOpsQuery = `${explorerPath.opsQuery} \"${path[path.length - 1]}\"`;
        onChangeExplorerPath(
          {
            ...explorerPath,
            opsQuery: nextOpsQuery,
          },
          'push',
        );
      }
    };
    const [openNodes, setOpenNodes] = React.useState<Set<string>>(new Set());
    const [selectedNode, setSelectedNode] = React.useState<null | {id: string; path: string}>(null);

    const rootNodes = React.useMemo(
      () =>
        Object.keys(assetGraphData.nodes)
          .filter(
            (id) =>
              // When we filter to a subgraph, the nodes at the root aren't real roots, but since
              // their upstream graph is cutoff we want to show them as roots in the sidebar.
              // Find these nodes by filtering on whether there parent nodes are in assetGraphData
              !Object.keys(assetGraphData.upstream[id] ?? {}).filter(
                (id) => assetGraphData.nodes[id],
              ).length,
          )
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
          const downstream = Object.keys(assetGraphData.downstream[node.id] || {}).filter(
            (id) => assetGraphData.nodes[id],
          );
          queue.unshift(
            ...downstream.map((id) => ({level: node.level + 1, id, path: `${node.path}:${id}`})),
          );
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
            if (!assetGraphData.nodes[next]) {
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
          setSelectedNode({id: lastSelectedNode.id, path: currentPath});
          return nextOpenNodes;
        });
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [lastSelectedNode, assetGraphData]);

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
              return allAssetKeys.map((key) => ({
                value: JSON.stringify(key.path),
                label: key.path[key.path.length - 1]!,
              }));
            }, [allAssetKeys])}
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

const Node = ({
  assetGraphData,
  node,
  level,
  toggleOpen,
  selectNode,
  isOpen,
  isSelected,
  selectThisNode,
  explorerPath,
  onChangeExplorerPath,
}: {
  assetGraphData: GraphData;
  node: GraphNode;
  level: number;
  toggleOpen: () => void;
  selectThisNode: (e: React.MouseEvent<any> | React.KeyboardEvent<any>) => void;
  selectNode: (e: React.MouseEvent<any> | React.KeyboardEvent<any>, nodeId: string) => void;
  isOpen: boolean;
  isSelected: boolean;
  explorerPath: ExplorerPath;
  onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
}) => {
  const displayName = getDisplayName(node);

  const upstream = Object.keys(assetGraphData.upstream[node.id] ?? {});
  const downstream = Object.keys(assetGraphData.downstream[node.id] ?? {});
  const elementRef = React.useRef<HTMLDivElement | null>(null);

  const [showDownstreamDialog, setShowDownstreamDialog] = React.useState(false);
  const [showUpstreamDialog, setShowUpstreamDialog] = React.useState(false);

  function showDownstreamGraph() {
    const path = JSON.parse(node.id);
    const nextOpsQuery = `${explorerPath.opsQuery} \"${path[path.length - 1]}\"*`;
    onChangeExplorerPath(
      {
        ...explorerPath,
        opsQuery: nextOpsQuery,
      },
      'push',
    );
  }

  function showUpstreamGraph() {
    const path = JSON.parse(node.id);
    const nextOpsQuery = `${explorerPath.opsQuery} *\"${path[path.length - 1]}\"`;
    onChangeExplorerPath(
      {
        ...explorerPath,
        opsQuery: nextOpsQuery,
      },
      'push',
    );
  }

  return (
    <>
      <UpstreamDownstreamDialog
        title="Downstream assets"
        assets={downstream}
        isOpen={showDownstreamDialog}
        close={() => {
          setShowDownstreamDialog(false);
        }}
        selectNode={(e, id) => {
          selectNode(e, id);
        }}
      />
      <UpstreamDownstreamDialog
        title="Upstream assets"
        assets={upstream}
        isOpen={showUpstreamDialog}
        close={() => {
          setShowUpstreamDialog(false);
        }}
        selectNode={selectNode}
      />
      <Box ref={elementRef} onClick={selectThisNode}>
        <BoxWrapper level={level}>
          <Box
            padding={{right: 12, vertical: 2}}
            flex={{direction: 'row', gap: 2, alignItems: 'center'}}
          >
            {downstream.filter((id) => assetGraphData.nodes[id]).length ? (
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
              <Popover
                content={
                  <Menu>
                    {/* TODO: Hook up materialization */}
                    <MenuItem icon="materialization" text="Materialize" />
                    {upstream.length ? (
                      <MenuItem
                        text="Select upstream"
                        icon="panel_show_left"
                        onClick={(e) => {
                          e.stopPropagation();
                          // TODO: Hook up selecting the nodes
                          showUpstreamGraph();
                        }}
                      />
                    ) : null}
                    {downstream.length ? (
                      <MenuItem
                        text="Select downstream"
                        icon="panel_show_right"
                        onClick={(e) => {
                          e.stopPropagation();
                          // TODO: Hook up selecting the nodes
                          showDownstreamGraph();
                        }}
                      />
                    ) : null}
                    {upstream.length ? (
                      <MenuItem
                        text="Show upstream graph"
                        icon="arrow_back"
                        onClick={(e) => {
                          e.stopPropagation();
                          showUpstreamGraph();
                        }}
                      />
                    ) : null}
                    {downstream.length ? (
                      <MenuItem
                        text="Show downstream graph"
                        icon="arrow_forward"
                        onClick={(e) => {
                          e.stopPropagation();
                          showDownstreamGraph();
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
  isOpen,
  close,
  selectNode,
}: {
  title: string;
  assets: string[];
  isOpen: boolean;
  close: () => void;
  selectNode: (e: React.MouseEvent<any> | React.KeyboardEvent<any>, nodeId: string) => void;
}) => {
  return (
    <Dialog isOpen={isOpen} onClose={close} title={title}>
      <DialogBody>
        <Menu>
          {assets.map((assetId) => {
            const path = JSON.parse(assetId);
            return (
              <MenuItem
                icon="asset"
                text={path[path.length - 1]}
                key={assetId}
                onClick={(e) => {
                  selectNode(e, assetId);
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
