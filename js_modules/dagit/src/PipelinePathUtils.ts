export interface PipelineExplorerPath {
  pipelineName: string;
  snapshotId?: string;
  solidsQuery: string;
  pathSolids: string[];
}

export function explorerPathToString(path: PipelineExplorerPath) {
  const root = [
    path.pipelineName,
    path.snapshotId ? `@${path.snapshotId}` : ``,
    path.solidsQuery ? `:${path.solidsQuery}` : ``,
  ].join('');

  return `${root}/${path.pathSolids.join('/')}`;
}

export function explorerPathFromString(path: string) {
  const [root, ...pathSolids] = path.split('/');
  const match = /^([^:@]+)@?([^:]+)?:?(.*)$/.exec(root);
  const [, pipelineName, snapshotId, solidsQuery] = [...(match || []), '', '', ''];

  return {
    pipelineName,
    snapshotId,
    solidsQuery,
    pathSolids,
  };
}
