import {Box, Menu, MenuDivider, MenuItem, Spinner} from '@dagster-io/ui-components';
import * as React from 'react';

import {GraphData, tokenForAssetKey} from './Utils';
import {StatusDot} from './sidebar/StatusDot';
import {useAssetBaseData} from '../asset-data/AssetBaseDataProvider';
import {useExecuteAssetMenuItem} from '../assets/AssetActionMenu';
import {
  AssetKeysDialog,
  AssetKeysDialogEmptyState,
  AssetKeysDialogHeader,
} from '../assets/AutoMaterializePolicyPage/AssetKeysDialog';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {AssetKeyInput} from '../graphql/types';
import {ExplorerPath} from '../pipelines/PipelinePathUtils';
import {MenuLink} from '../ui/MenuLink';
import {VirtualizedItemListForDialog} from '../ui/VirtualizedItemListForDialog';

export type AssetNodeMenuNode = {
  id: string;
  assetKey: AssetKeyInput;
  definition: {
    isMaterializable: boolean;
    isObservable: boolean;
    isExecutable: boolean;
    isPartitioned: boolean;
    hasMaterializePermission: boolean;
  };
};

export type AssetNodeMenuProps = {
  node: AssetNodeMenuNode;
  graphData?: GraphData;
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
  const upstream = graphData ? Object.keys(graphData.upstream[node.id] ?? {}) : [];
  const downstream = graphData ? Object.keys(graphData.downstream[node.id] ?? {}) : [];

  const asset = React.useMemo(
    () => ({assetKey: node.assetKey, ...node.definition}),
    [node.definition, node.assetKey],
  );
  const {executeItem, launchpadElement} = useExecuteAssetMenuItem(asset);

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

  const {liveData} = useAssetBaseData(node.assetKey, 'context-menu');

  const isObservable = node.definition.isObservable;
  const lastMaterializationRunID = liveData?.lastMaterialization?.runId;
  const lastObservationID = liveData?.lastObservation?.runId;

  return {
    menu: (
      <Menu>
        <MenuLink
          to={assetDetailsPathForKey(node.assetKey)}
          text="View asset details"
          icon="asset"
        />
        {node.definition?.isExecutable ? (
          <MenuLink
            icon="history"
            disabled={!lastMaterializationRunID && !lastObservationID}
            to={`/runs/${lastMaterializationRunID || lastObservationID}`}
            text={
              <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                View latest {isObservable ? 'observation' : 'materialization'}
                {liveData ? null : <Spinner purpose="caption-text" />}
              </Box>
            }
          />
        ) : null}
        <MenuDivider />
        {executeItem}
        {executeItem && (upstream.length || downstream.length) ? <MenuDivider /> : null}
        {upstream.length && graphData ? (
          <MenuItem
            text={`View parents (${upstream.length})`}
            icon="list"
            onClick={() => {
              setShowParents(true);
            }}
          />
        ) : null}
        {upstream.length || !graphData ? (
          <MenuItem
            text="Show upstream graph"
            icon="arrow_back"
            onClick={() => showGraph(`*\"${tokenForAssetKey(node.assetKey)}\"`)}
          />
        ) : null}
        {downstream.length || !graphData ? (
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
        {graphData && (
          <UpstreamDownstreamDialog
            title="Parent assets"
            graphData={graphData}
            assetKeys={upstream}
            isOpen={showParents}
            setIsOpen={setShowParents}
            selectNode={selectNode}
          />
        )}
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
