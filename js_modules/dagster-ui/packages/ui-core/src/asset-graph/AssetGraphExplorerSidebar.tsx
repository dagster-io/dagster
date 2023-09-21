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
  MenuDivider,
  Spinner,
  ButtonGroup,
  Tooltip,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React from 'react';
import styled from 'styled-components';

import {showSharedToaster} from '../app/DomUtils';
import {useMaterializationAction} from '../assets/LaunchAssetExecutionButton';
import {AssetKey} from '../assets/types';
import {ExplorerPath} from '../pipelines/PipelinePathUtils';
import {Container, Inner, Row} from '../ui/VirtualizedTable';
import {buildRepoPathForHuman} from '../workspace/buildRepoAddress';

import {GraphData, GraphNode, tokenForAssetKey} from './Utils';

const COLLATOR = new Intl.Collator(navigator.language, {sensitivity: 'base', numeric: true});

type FolderNodeNonAssetType =
  | {groupName: string; id: string; level: number}
  | {locationName: string; id: string; level: number};

type FolderNodeType = FolderNodeNonAssetType | {path: string; id: string; level: number};

type TreeNodeType = {level: number; id: string; path: string};

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
          const nextOpsQuery = `${explorerPath.opsQuery} \"${tokenForAssetKey({path})}\"`;
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

    const [viewType, setViewType] = React.useState<'tree' | 'folder'>('tree');

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

    const folderNodes = React.useMemo(() => {
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

      return folderNodes;
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
      if (lastSelectedNode) {
        setOpenNodes((prevOpenNodes) => {
          if (viewType === 'folder') {
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
        renderedNodes.findIndex((node) => nodeId(lastSelectedNode) === nodeId(node)),
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
          return renderedNodes.findIndex((node) => nodeId(node) === nodeId(selectedNode));
        }
      },
      // eslint-disable-next-line react-hooks/exhaustive-deps
      [viewType, renderedNodes, selectedNode],
    );

    React.useLayoutEffect(() => {
      if (indexOfLastSelectedNode !== -1) {
        rowVirtualizer.scrollToIndex(indexOfLastSelectedNode);
      }
    }, [indexOfLastSelectedNode, rowVirtualizer]);

    return (
      <div style={{display: 'grid', gridTemplateRows: 'auto auto minmax(0, 1fr)', height: '100%'}}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr auto',
            gap: '6px',
            padding: '12px 24px',
            borderBottom: `1px solid ${Colors.KeylineGray}`,
          }}
        >
          <ButtonGroupWrapper>
            <ButtonGroup
              activeItems={new Set([viewType])}
              buttons={[
                {id: 'tree', label: 'Tree view', icon: 'gantt_flat'},
                {id: 'folder', label: 'Folder view', icon: 'folder_open'},
              ]}
              onClick={(id: 'tree' | 'folder') => {
                setViewType(id);
              }}
            />
          </ButtonGroupWrapper>
          <Tooltip content="Hide sidebar">
            <Button icon={<Icon name="panel_show_right" />} onClick={hideSidebar} />
          </Tooltip>
        </div>
        <Box padding={{vertical: 8, horizontal: 24}}>
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
                        isOpen={openNodes.has(nodeId(node))}
                        graphData={graphData}
                        node={row}
                        level={node.level}
                        isSelected={
                          selectedNode && 'path' in node && 'path' in selectedNode
                            ? selectedNode.path === node.path
                            : selectedNode?.id === node.id
                        }
                        toggleOpen={() => {
                          setSelectedNode(node);
                          setOpenNodes((nodes) => {
                            const openNodes = new Set(nodes);
                            const isOpen = openNodes.has(nodeId(node));
                            if (isOpen) {
                              openNodes.delete(nodeId(node));
                            } else {
                              openNodes.add(nodeId(node));
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
  graphData,
  node,
  level,
  toggleOpen,
  selectNode,
  isOpen,
  isSelected,
  selectThisNode,
  explorerPath,
  onChangeExplorerPath,
  viewType,
}: {
  graphData: GraphData;
  node: GraphNode | FolderNodeNonAssetType;
  level: number;
  toggleOpen: () => void;
  selectThisNode: (e: React.MouseEvent<any> | React.KeyboardEvent<any>) => void;
  selectNode: (e: React.MouseEvent<any> | React.KeyboardEvent<any>, nodeId: string) => void;
  isOpen: boolean;
  isSelected: boolean;
  explorerPath: ExplorerPath;
  onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
  viewType: 'tree' | 'folder';
}) => {
  const isGroupNode = 'groupName' in node;
  const isLocationNode = 'locationName' in node;
  const isAssetNode = !isGroupNode && !isLocationNode;

  const displayName = React.useMemo(() => {
    if (isAssetNode) {
      return getDisplayName(node);
    } else if (isGroupNode) {
      return node.groupName;
    } else {
      return node.locationName;
    }
  }, [isAssetNode, isGroupNode, node]);

  const upstream = Object.keys(graphData.upstream[node.id] ?? {});
  const downstream = Object.keys(graphData.downstream[node.id] ?? {});
  const elementRef = React.useRef<HTMLDivElement | null>(null);

  const [showParents, setShowParents] = React.useState(false);

  function showDownstreamGraph() {
    const path = JSON.parse(node.id);
    const newQuery = `\"${tokenForAssetKey({path})}\"*`;
    const nextOpsQuery = explorerPath.opsQuery.includes(newQuery)
      ? explorerPath.opsQuery
      : `${explorerPath.opsQuery} ${newQuery}`;
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
    const newQuery = `*\"${tokenForAssetKey({path})}\"`;
    const nextOpsQuery = explorerPath.opsQuery.includes(newQuery)
      ? explorerPath.opsQuery
      : `${explorerPath.opsQuery} ${newQuery}`;
    onChangeExplorerPath(
      {
        ...explorerPath,
        opsQuery: nextOpsQuery,
      },
      'push',
    );
  }

  const {onClick, loading, launchpadElement} = useMaterializationAction();

  return (
    <>
      {launchpadElement}
      <UpstreamDownstreamDialog
        title="Parent assets"
        assets={upstream}
        isOpen={showParents}
        close={() => {
          setShowParents(false);
        }}
        selectNode={selectNode}
      />
      <Box ref={elementRef} onClick={selectThisNode}>
        <BoxWrapper level={level}>
          <Box padding={{right: 12}} flex={{direction: 'row', gap: 2, alignItems: 'center'}}>
            {!isAssetNode ||
            (viewType === 'tree' && downstream.filter((id) => graphData.nodes[id]).length) ? (
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
                gap: 6,
                grow: 1,
                shrink: 1,
              }}
              padding={{horizontal: 8, vertical: 5 as any}}
              style={{
                width: '100%',
                borderRadius: '8px',
                ...(isSelected ? {background: Colors.LightPurple} : {}),
              }}
            >
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns:
                    isGroupNode || isLocationNode ? 'auto minmax(0, 1fr)' : 'minmax(0, 1fr)',
                  gap: '6px',
                }}
              >
                {isGroupNode ? <Icon name="asset_group" /> : null}
                {isLocationNode ? <Icon name="folder_open" /> : null}
                <MiddleTruncate text={displayName} />
              </div>
              {isAssetNode ? (
                <div
                  onClick={(e) => {
                    // stop propagation outside of the popover to prevent parent onClick from being selected
                    e.stopPropagation();
                  }}
                >
                  <Popover
                    content={
                      <Menu>
                        <MenuItem
                          icon="materialization"
                          text={
                            <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                              <span>Materialize</span>
                              {loading ? <Spinner purpose="body-text" /> : null}
                            </Box>
                          }
                          onClick={async (e) => {
                            await showSharedToaster({
                              intent: 'primary',
                              message: 'Initiating materialization',
                              icon: 'materialization',
                            });
                            onClick([node.assetKey], e, false);
                          }}
                        />
                        {upstream.length || downstream.length ? <MenuDivider /> : null}
                        {upstream.length > 1 ? (
                          <MenuItem
                            text={`View parents (${upstream.length})`}
                            icon="list"
                            onClick={() => {
                              setShowParents(true);
                            }}
                          />
                        ) : null}
                        {upstream.length ? (
                          <MenuItem
                            text="Show upstream graph"
                            icon="arrow_back"
                            onClick={showUpstreamGraph}
                          />
                        ) : null}
                        {downstream.length ? (
                          <MenuItem
                            text="Show downstream graph"
                            icon="arrow_forward"
                            onClick={showDownstreamGraph}
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
                </div>
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
        <Box
          padding={{left: 8}}
          margin={{left: 8}}
          border={{side: 'left', width: 1, color: Colors.KeylineGray}}
        >
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

const ButtonGroupWrapper = styled.div`
  > * {
    display: grid;
    grid-template-columns: 1fr 1fr;
    > * {
      place-content: center;
    }
  }
`;

function nodeId(node: {path: string; id: string} | {id: string}) {
  return 'path' in node ? node.path : node.id;
}
