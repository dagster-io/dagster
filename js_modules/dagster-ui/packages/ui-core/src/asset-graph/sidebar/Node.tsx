import {
  Box,
  Colors,
  Icon,
  Menu,
  MenuItem,
  Popover,
  MiddleTruncate,
  MenuDivider,
  Spinner,
} from '@dagster-io/ui-components';
import React from 'react';
import styled from 'styled-components';

import {showSharedToaster} from '../../app/DomUtils';
import {
  AssetKeysDialog,
  AssetKeysDialogEmptyState,
  AssetKeysDialogHeader,
} from '../../assets/AutoMaterializePolicyPage/AssetKeysDialog';
import {useMaterializationAction} from '../../assets/LaunchAssetExecutionButton';
import {ExplorerPath} from '../../pipelines/PipelinePathUtils';
import {VirtualizedItemListForDialog} from '../../ui/VirtualizedItemListForDialog';
import {GraphData, GraphNode, tokenForAssetKey} from '../Utils';

import {FolderNodeNonAssetType, getDisplayName} from './util';

import {getDisplayName} from './util';

export const Node = ({
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

  const {onClick, loading, launchpadElement} = useMaterializationAction();

  return (
    <>
      {launchpadElement}
      <UpstreamDownstreamDialog
        title="Parent assets"
        assetKeys={upstream}
        isOpen={showParents}
        setIsOpen={setShowParents}
        selectNode={selectNode}
      />
      <Box ref={elementRef} onClick={selectThisNode} padding={{left: 8}}>
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
                ...(isSelected ? {background: Colors.Blue50} : {}),
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
                      <Icon name="more_horiz" color={Colors.Gray500} />
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
  assetKeys,
  isOpen,
  setIsOpen,
  selectNode,
}: {
  title: string;
  assetKeys: string[];
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
  selectNode: (e: React.MouseEvent<any> | React.KeyboardEvent<any>, nodeId: string) => void;
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
                return (
                  <MenuItem
                    icon="asset"
                    text={path[path.length - 1]}
                    key={assetId}
                    onClick={(e) => {
                      selectNode(e, assetId);
                      setIsOpen(false);
                    }}
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

const BoxWrapper = ({level, children}: {level: number; children: React.ReactNode}) => {
  const wrapper = React.useMemo(() => {
    let sofar = children;
    for (let i = 0; i < level; i++) {
      sofar = (
        <Box
          padding={{left: 8}}
          margin={{left: 8}}
          border={{side: 'left', width: 1, color: Colors.KeylineGray}}
          style={{position: 'relative'}}
        >
          {sofar}
        </Box>
      );
    }
    return sofar;
  }, [level, children]);

  return <>{wrapper}</>;
};

const ExpandMore = styled.div``;

const GrayOnHoverBox = styled(Box)`
  border-radius: 8px;
  cursor: pointer;
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
