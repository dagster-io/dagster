import * as React from 'react';
import {Redirect, useLocation, useRouteMatch} from 'react-router-dom';

import {LoadingWithProgress} from 'src/Loading';
import {explorerPathFromString} from 'src/PipelinePathUtils';
import {
  DagsterRepoOption,
  optionToRepoAddress,
  useRepositoryOptions,
} from 'src/workspace/WorkspaceContext';
import {WorkspacePipelineDisambiguationRoot} from 'src/workspace/WorkspacePipelineDisambiguationRoot';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

const findMatch = (
  options: DagsterRepoOption[],
  pipelineName: string,
  snapshotId: string | null,
) => {
  if (options.length) {
    return options.find((repo) => {
      return repo.repository.pipelines.find(
        (pipeline) =>
          pipeline.name === pipelineName &&
          (!snapshotId || pipeline.pipelineSnapshotId === snapshotId),
      );
    });
  }
  return null;
};

interface Props {
  pipelinePath: string;
}

export const WorkspacePipelineRoot: React.FC<Props> = (props) => {
  const {pipelinePath} = props;
  const entireMatch = useRouteMatch('/workspace/pipelines/(/?.*)');
  const location = useLocation();

  const toAppend = entireMatch!.params[0];
  const {search} = location;

  const {pipelineName, snapshotId} = explorerPathFromString(pipelinePath);
  const {loading, options} = useRepositoryOptions();

  if (loading) {
    return <LoadingWithProgress />;
  }

  const repoWithMatch = findMatch(options, pipelineName, snapshotId);
  if (repoWithMatch) {
    const repoAddress = optionToRepoAddress(repoWithMatch);
    const to = workspacePathFromAddress(repoAddress, `/pipelines/${toAppend}${search}`);
    return <Redirect to={to} />;
  }

  return <WorkspacePipelineDisambiguationRoot pipelineName={pipelineName} />;
};
