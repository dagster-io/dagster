import {DagsterRepoOption} from './WorkspaceContext/util';

export const repoContainsPipeline = (
  repo: DagsterRepoOption,
  pipelineName: string,
  snapshotId?: string,
) => {
  return repo.repository.pipelines.find(
    (pipeline) =>
      pipeline.name === pipelineName && (!snapshotId || snapshotId === pipeline.pipelineSnapshotId),
  );
};

export const findRepoContainingPipeline = (
  options: DagsterRepoOption[],
  pipelineName: string,
  snapshotId?: string,
) => {
  return (options || []).filter((repo) => repoContainsPipeline(repo, pipelineName, snapshotId));
};
