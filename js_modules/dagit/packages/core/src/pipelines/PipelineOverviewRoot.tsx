import * as React from 'react';
import {useHistory, useLocation, useParams} from 'react-router-dom';

import {buildPipelineSelector, isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {GraphExplorerJobContext} from './GraphExplorerJobContext';
import {PipelineExplorerContainer} from './PipelineExplorerRoot';
import {
  explorerPathFromString,
  explorerPathToString,
  ExplorerPath,
  useStripSnapshotFromPath,
} from './PipelinePathUtils';
import {SidebarPipelineOrJobOverview} from './SidebarPipelineOrJobOverview';
import {useJobTitle} from './useJobTitle';

interface Props {
  repoAddress: RepoAddress;
}

export const PipelineOverviewRoot: React.FC<Props> = (props) => {
  const {repoAddress} = props;
  const history = useHistory();
  const location = useLocation();
  const params = useParams();

  const explorerPath = explorerPathFromString(params['0']);

  const repo = useRepository(repoAddress);
  const pipelineSelector = buildPipelineSelector(repoAddress, explorerPath.pipelineName);
  const isJob = isThisThingAJob(repo, explorerPath.pipelineName);

  useJobTitle(explorerPath, isJob);
  useStripSnapshotFromPath({pipelinePath: explorerPathToString(explorerPath)});

  const onChangeExplorerPath = React.useCallback(
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

  return (
    <GraphExplorerJobContext.Provider
      value={{
        sidebarTab: <SidebarPipelineOrJobOverview pipelineSelector={pipelineSelector} />,
      }}
    >
      <PipelineExplorerContainer
        repoAddress={repoAddress}
        explorerPath={explorerPath}
        onChangeExplorerPath={onChangeExplorerPath}
      />
    </GraphExplorerJobContext.Provider>
  );
};
