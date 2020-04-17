export interface PipelineSelector {
  pipelineName: string;
  snapshotId?: string;
  solidsQuery: string;
  path: string[];
}

export function selectorToString(selector: PipelineSelector) {
  const root = [
    selector.pipelineName,
    selector.snapshotId ? `@${selector.snapshotId}` : ``,
    selector.solidsQuery ? `:${selector.solidsQuery}` : ``
  ].join("");

  return `${root}/${selector.path.join("/")}`;
}

export function selectorFromString(selector: string) {
  const [root, ...pathSolids] = selector.split("/");
  const match = /^([^:@]+)@?([^:]+)?:?(.*)$/.exec(root);
  const [, pipeline, snapshotId, solidsQuery] = [...(match || []), "", "", ""];

  return {
    pipelineName: pipeline,
    snapshotId: snapshotId,
    solidsQuery: solidsQuery,
    path: pathSolids
  };
}
