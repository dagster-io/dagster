import React from 'react';
import {Link} from 'react-router-dom';

import {FontFamily} from 'src/ui/styles';

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

export const PipelineSnapshotLink: React.FunctionComponent<{
  pipelineName: string;
  snapshotId: string;
}> = (props) => {
  const snapshotLink = `/instance/snapshots/${explorerPathToString({
    pipelineName: props.pipelineName,
    snapshotId: props.snapshotId,
    solidsQuery: '',
    pathSolids: [],
  })}`;

  return (
    <div style={{fontFamily: FontFamily.monospace}}>
      <Link to={snapshotLink}>{props.snapshotId.slice(0, 8)}</Link>
    </div>
  );
};
