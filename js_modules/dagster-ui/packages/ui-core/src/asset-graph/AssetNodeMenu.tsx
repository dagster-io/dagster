import {Box, Menu, MenuDivider, MenuItem, Spinner} from '@dagster-io/ui-components';
import * as React from 'react';

import {GraphData, GraphNode, tokenForAssetKey} from './Utils';
import {StatusDot} from './sidebar/StatusDot';
import {showSharedToaster} from '../app/DomUtils';
import {
  AssetKeysDialog,
  AssetKeysDialogEmptyState,
  AssetKeysDialogHeader,
} from '../assets/AutoMaterializePolicyPage/AssetKeysDialog';
import {useMaterializationAction} from '../assets/LaunchAssetExecutionButton';
import {ExplorerPath} from '../pipelines/PipelinePathUtils';
import {VirtualizedItemListForDialog} from '../ui/VirtualizedItemListForDialog';

export type AssetNodeMenuProps = {
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
}: AssetNodeMenuProps) => {
  const upstream = Object.keys(graphData.upstream[node.id] ?? {});
  const downstream = Object.keys(graphData.downstream[node.id] ?? {});

  const {onClick, loading, launchpadElement} = useMaterializationAction();

  const [showParents, setShowParents] = React.useState(false);

  function showGraph(newQuery: string) {
    if (!explorerPath || !onChangeExplorerPath) {
      return;
    }
    const nextOpsQuery = explorerPath.opsQuery.includes(newQuery)
      ? explorerPath.opsQuery
      : newQuery;
    onChangeExplorerPath({...explorerPath, opsQuery: nextOpsQuery}, 'push');
  }

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
            onClick={() => showGraph(`*\"${tokenForAssetKey(node.assetKey)}\"`)}
          />
        ) : null}
        {downstream.length ? (
          <MenuItem
            text="Show downstream graph"
            icon="arrow_forward"
            onClick={() => showGraph(`\"${tokenForAssetKey(node.assetKey)}\"*`)}
          />
        ) : null}
      </Menu>
    ),
    dialog: (
      <>
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
