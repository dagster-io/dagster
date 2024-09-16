import {useCallback, useMemo} from 'react';
import {useHistory, useLocation, useParams} from 'react-router-dom';
import {PipelineExplorerContainer} from 'shared/pipelines/PipelineExplorerRoot.oss';

import {
  ExplorerPath,
  explorerPathFromString,
  explorerPathToString,
  useStripSnapshotFromPath,
} from './PipelinePathUtils';
import {useJobTitle} from './useJobTitle';
import {useTrackPageView} from '../app/analytics';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {AssetLocation} from '../asset-graph/useFindAssetLocation';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext/util';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

interface Props {
  repoAddress: RepoAddress;
}

export const PipelineOverviewRoot = (props: Props) => {
  useTrackPageView();

  const {repoAddress} = props;
  const history = useHistory();
  const location = useLocation();
  const params = useParams();
  const pathStr = (params as any)['0'];
  const explorerPath = useMemo(() => explorerPathFromString(pathStr), [pathStr]);

  const repo = useRepository(repoAddress);
  const isJob = isThisThingAJob(repo, explorerPath.pipelineName);

  useJobTitle(explorerPath, isJob);
  useStripSnapshotFromPath({pipelinePath: explorerPathToString(explorerPath)});

  const onChangeExplorerPath = useCallback(
    (path: ExplorerPath, action: 'push' | 'replace') => {
      history[action]({
        search: location.search,
        pathname: workspacePathFromAddress(
          repoAddress,
          `/${isJob ? 'jobs' : 'pipelines'}/${explorerPathToString(path)}`,
        ),
      });
    },
    [history, location.search, repoAddress, isJob],
  );

  const onNavigateToSourceAssetNode = useCallback(
    (e: Pick<React.MouseEvent<any>, 'metaKey'>, node: AssetLocation) => {
      if (!node.jobName || !node.opNames.length || !node.repoAddress) {
        // This op has no definition in any loaded repository (source asset).
        // The best we can do is show the asset page. This will still be mostly empty,
        // but there can be a description.
        const path = assetDetailsPathForKey(node.assetKey, {view: 'definition'});
        if (e.metaKey) {
          window.open(path, '_blank');
        } else {
          history.push(path);
        }
        return;
      }

      // Note: asset location can be in another job AND in another repo! Need
      // to build a full job URL using the `node` info here.
      history.replace({
        search: location.search,
        pathname: workspacePathFromAddress(
          node.repoAddress,
          `/jobs/${explorerPathToString({
            ...explorerPath,
            opNames: [tokenForAssetKey(node.assetKey)],
            opsQuery: '',
            pipelineName: node.jobName!,
          })}`,
        ),
      });
    },
    [explorerPath, history, location.search],
  );

  return (
    <PipelineExplorerContainer
      repoAddress={repoAddress}
      explorerPath={explorerPath}
      onChangeExplorerPath={onChangeExplorerPath}
      onNavigateToSourceAssetNode={onNavigateToSourceAssetNode}
    />
  );
};
