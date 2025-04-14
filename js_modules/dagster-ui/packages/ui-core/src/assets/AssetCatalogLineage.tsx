import React, {useCallback, useMemo} from 'react';
import {useHistory} from 'react-router';

import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {AssetGraphExplorer} from '../asset-graph/AssetGraphExplorer';
import {AssetGraphViewType} from '../asset-graph/Utils';
import {AssetLocation} from '../asset-graph/useFindAssetLocation';
import {useOpenInNewTab} from '../hooks/useOpenInNewTab';
import {ExplorerPath} from '../pipelines/PipelinePathUtils';
import {workspacePathFromAddress} from '../workspace/workspacePath';

export const AssetCatalogLineage = React.memo(
  ({
    selection,
    onChangeSelection,
    isFullScreen,
    toggleFullScreen,
  }: {
    selection: string;
    onChangeSelection: (selection: string) => void;
    isFullScreen: boolean;
    toggleFullScreen: () => void;
  }) => {
    const history = useHistory();
    const openInNewTab = useOpenInNewTab();

    const onNavigateToSourceAssetNode = useCallback(
      (e: Pick<React.MouseEvent<any>, 'metaKey'>, node: AssetLocation) => {
        let path;
        if (node.groupName && node.repoAddress) {
          path = workspacePathFromAddress(
            node.repoAddress,
            `/asset-groups/${node.groupName}/lineage/${node.assetKey.path
              .map(encodeURIComponent)
              .join('/')}`,
          );
        } else {
          path = assetDetailsPathForKey(node.assetKey, {view: 'definition'});
        }
        if (e.metaKey) {
          openInNewTab(path);
        } else {
          history.push(path);
        }
      },
      [history, openInNewTab],
    );

    const fetchOptions = React.useMemo(() => ({loading: false}), []);

    const lineageOptions = React.useMemo(
      () => ({preferAssetRendering: true, explodeComposites: true}),
      [],
    );

    return (
      <AssetGraphExplorer
        fetchOptions={fetchOptions}
        options={lineageOptions}
        explorerPath={useMemo(
          () => ({
            opsQuery: selection,
            pipelineName: '',
            opNames: [''],
          }),
          [selection],
        )}
        onChangeExplorerPath={useCallback(
          (path: ExplorerPath) => onChangeSelection(path.opsQuery),
          [onChangeSelection],
        )}
        onNavigateToSourceAssetNode={onNavigateToSourceAssetNode}
        viewType={AssetGraphViewType.CATALOG}
        isFullScreen={isFullScreen}
        toggleFullScreen={toggleFullScreen}
      />
    );
  },
);
