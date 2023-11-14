import {
  Menu,
  MenuItem,
  Spinner,
  MenuDivider,
  Box,
  Dialog,
  DialogBody,
  DialogFooter,
  Button,
  Checkbox,
  Colors,
  Icon,
  MiddleTruncate,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {showSharedToaster} from '../app/DomUtils';
import {
  AssetKeysDialog,
  AssetKeysDialogHeader,
  AssetKeysDialogEmptyState,
} from '../assets/AutoMaterializePolicyPage/AssetKeysDialog';
import {useMaterializationAction} from '../assets/LaunchAssetExecutionButton';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {ExplorerPath} from '../pipelines/PipelinePathUtils';
import {VirtualizedItemListForDialog} from '../ui/VirtualizedItemListForDialog';
import {Container, Inner, Row} from '../ui/VirtualizedTable';

import {
  GraphData,
  GraphNode,
  displayNameForAssetKey,
  getUpstreamNodes,
  toGraphId,
  tokenForAssetKey,
} from './Utils';
import {StatusDot} from './sidebar/StatusDot';
import {AssetNodeKeyFragment} from './types/AssetNode.types';

type Props = {
  graphData: GraphData;
  node: GraphNode;
  explorerPath?: ExplorerPath;
  onChangeExplorerPath?: (path: ExplorerPath, mode: 'replace' | 'push') => void;
  selectNode?: (e: React.MouseEvent<any> | React.KeyboardEvent<any>, nodeId: string) => void;
};
export const useAssetNodeMenu = ({
  node,
  selectNode,
  graphData,
  explorerPath,
  onChangeExplorerPath,
}: Props) => {
  const upstream = Object.keys(graphData.upstream[node.id] ?? {});
  const downstream = Object.keys(graphData.downstream[node.id] ?? {});

  const {onClick, loading, launchpadElement} = useMaterializationAction();

  const [showParents, setShowParents] = React.useState(false);

  function showDownstreamGraph() {
    if (!explorerPath || !onChangeExplorerPath) {
      return;
    }
    const path = JSON.parse(node.id);
    const newQuery = `\"${tokenForAssetKey({path})}\"*`;
    const nextOpsQuery = explorerPath.opsQuery.includes(newQuery)
      ? explorerPath.opsQuery
      : newQuery;
    onChangeExplorerPath(
      {
        ...explorerPath,
        opsQuery: nextOpsQuery,
      },
      'push',
    );
  }

  function showUpstreamGraph() {
    if (!explorerPath || !onChangeExplorerPath) {
      return;
    }
    const path = JSON.parse(node.id);
    const newQuery = `*\"${tokenForAssetKey({path})}\"`;
    const nextOpsQuery = explorerPath.opsQuery.includes(newQuery)
      ? explorerPath.opsQuery
      : newQuery;
    onChangeExplorerPath(
      {
        ...explorerPath,
        opsQuery: nextOpsQuery,
      },
      'push',
    );
  }

  const [showMaterializeWithUpstreamDialog, setShowMaterializeWithUpstreamDialog] =
    React.useState(false);

  return {
    menu: (
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
        {upstream.length ? (
          <MenuItem
            icon="materialization"
            text={
              <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                <span>Materialize with upstream</span>
                {loading ? <Spinner purpose="body-text" /> : null}
              </Box>
            }
            onClick={() => {
              setShowMaterializeWithUpstreamDialog(true);
            }}
          />
        ) : null}
        {upstream.length || downstream.length ? <MenuDivider /> : null}
        {upstream.length ? (
          <MenuItem
            text={`View parents (${upstream.length})`}
            icon="list"
            onClick={() => {
              setShowParents(true);
            }}
          />
        ) : null}
        {upstream.length ? (
          <MenuItem text="Show upstream graph" icon="arrow_back" onClick={showUpstreamGraph} />
        ) : null}
        {downstream.length ? (
          <MenuItem
            text="Show downstream graph"
            icon="arrow_forward"
            onClick={showDownstreamGraph}
          />
        ) : null}
      </Menu>
    ),
    dialog: (
      <>
        <MaterializeWithUpstreamDialog
          assetKeys={
            showMaterializeWithUpstreamDialog ? getUpstreamNodes(node.assetKey, graphData) : []
          }
          isOpen={showMaterializeWithUpstreamDialog}
          close={() => setShowMaterializeWithUpstreamDialog(false)}
          onMaterialize={onClick}
          graphData={graphData}
        />
        <UpstreamDownstreamDialog
          title="Parent assets"
          graphData={graphData}
          assetKeys={upstream}
          isOpen={showParents}
          setIsOpen={setShowParents}
          selectNode={selectNode}
        />
        {launchpadElement}
      </>
    ),
  };
};

const UpstreamDownstreamDialog = ({
  title,
  graphData,
  assetKeys,
  isOpen,
  setIsOpen,
  selectNode,
}: {
  title: string;
  graphData: GraphData;
  assetKeys: string[];
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
  selectNode?: (e: React.MouseEvent<any> | React.KeyboardEvent<any>, nodeId: string) => void;
}) => {
  const [queryString, setQueryString] = React.useState('');

  const filteredAssetKeys = React.useMemo(() => {
    return assetKeys.filter((assetKey) => {
      const path = JSON.parse(assetKey);
      return path[path.length - 1].toLowerCase().includes(queryString.toLowerCase());
    });
  }, [assetKeys, queryString]);
  return (
    <AssetKeysDialog
      isOpen={isOpen}
      setIsOpen={setIsOpen}
      header={
        <AssetKeysDialogHeader
          title={title}
          showSearch={assetKeys.length > 0}
          placeholder="Filter by asset key…"
          queryString={queryString}
          setQueryString={setQueryString}
        />
      }
      content={
        queryString && !filteredAssetKeys.length ? (
          <AssetKeysDialogEmptyState
            title="No matching asset keys"
            description={
              <>
                No matching asset keys for <strong>{queryString}</strong>
              </>
            }
          />
        ) : (
          <Menu>
            <VirtualizedItemListForDialog
              items={filteredAssetKeys}
              itemBorders={false}
              renderItem={(assetId) => {
                const path = JSON.parse(assetId);
                const node = graphData.nodes[assetId];
                return (
                  <MenuItem
                    icon="asset"
                    text={
                      <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                        {node ? <StatusDot node={node} /> : null}
                        <span>{path[path.length - 1]}</span>
                      </Box>
                    }
                    key={assetId}
                    onClick={
                      selectNode
                        ? (e) => {
                            selectNode(e, assetId);
                            setIsOpen(false);
                          }
                        : undefined
                    }
                  />
                );
              }}
            />
          </Menu>
        )
      }
    />
  );
};

const MaterializeWithUpstreamDialog = React.memo(
  ({
    assetKeys,
    close,
    isOpen,
    onMaterialize,
    graphData,
  }: {
    assetKeys: AssetNodeKeyFragment[];
    isOpen: boolean;
    close: () => void;
    onMaterialize: ReturnType<typeof useMaterializationAction>['onClick'];
    graphData: GraphData;
  }) => {
    const materialize = async (e: React.MouseEvent<HTMLElement>) => {
      await showSharedToaster({
        intent: 'primary',
        message: 'Initiating materialization',
        icon: 'materialization',
      });
      onMaterialize(assetKeys, e, false);
    };
    const containerRef = React.useRef<HTMLDivElement | null>(null);
    const virtualizer = useVirtualizer({
      count: assetKeys?.length ?? 0,
      getScrollElement: () => containerRef.current,
      estimateSize: () => 28,
    });
    const totalHeight = virtualizer.getTotalSize();
    const items = virtualizer.getVirtualItems();

    const [checked, setChecked] = React.useState<Set<AssetNodeKeyFragment>>(new Set());
    React.useLayoutEffect(() => {
      setChecked(new Set(assetKeys));
    }, [assetKeys]);

    const [opened, setOpened] = React.useState(false);

    return (
      <Dialog
        isOpen={isOpen}
        onClose={close}
        onOpened={() => {
          setOpened(true);
        }}
        onClosed={() => {
          setOpened(false);
        }}
        title="Materialize with upstream"
        icon="materialization"
      >
        {/* Change they key after the openning animation to force MiddleTruncates to re-render and re-measure */}
        <DialogBody key={opened ? '1' : '0'}>
          <div style={{scale: 1}}>
            <RowGrid border="bottom" padding={{bottom: 8}}>
              <Checkbox
                id="check-all"
                checked={checked.size === assetKeys.length}
                onChange={() => {
                  setChecked((checked) => {
                    if (checked.size === assetKeys.length) {
                      return new Set();
                    } else {
                      return new Set(assetKeys);
                    }
                  });
                }}
              />
              <label htmlFor="check-all" style={{color: Colors.Gray500, cursor: 'pointer'}}>
                Asset Name
              </label>
            </RowGrid>
            <Container ref={containerRef} style={{maxHeight: '400px'}}>
              <Inner $totalHeight={totalHeight}>
                {items.map(({index, key, size, start, measureElement}) => {
                  const item = assetKeys[index]!;
                  return (
                    <Row $height={size} $start={start} key={key} ref={measureElement}>
                      <RowGrid border="bottom">
                        <Checkbox
                          id={`checkbox-${key}`}
                          checked={checked.has(item)}
                          onChange={() => {
                            setChecked((checked) => {
                              const copy = new Set(checked);
                              if (copy.has(item)) {
                                copy.delete(item);
                              } else {
                                copy.add(item);
                              }
                              return copy;
                            });
                          }}
                        />
                        <Box
                          as="label"
                          htmlFor={`checkbox-${key}`}
                          flex={{alignItems: 'center', gap: 4}}
                          style={{cursor: 'pointer'}}
                        >
                          <Box style={{overflow: 'hidden'}}>
                            <MiddleTruncate text={displayNameForAssetKey(item)} />
                          </Box>
                          <Link to={assetDetailsPathForKey(item)} target="_blank">
                            <Icon name="open_in_new" color={Colors.Link} />
                          </Link>
                        </Box>
                        <StatusDot node={graphData.nodes[toGraphId(item)]!} />
                      </RowGrid>
                    </Row>
                  );
                })}
              </Inner>
            </Container>
          </div>
        </DialogBody>
        <DialogFooter topBorder>
          <Button onClick={close}>Cancel</Button>
          <Button intent="primary" onClick={materialize}>
            Materialize
          </Button>
        </DialogFooter>
      </Dialog>
    );
  },
);

const TEMPLATE_COLUMNS = '20px minmax(0, 1fr) 32px ';

const RowGrid = styled(Box)`
  display: grid;
  grid-template-columns: ${TEMPLATE_COLUMNS};
  gap: 8px;
  height: 100%;
  align-items: center;
`;
