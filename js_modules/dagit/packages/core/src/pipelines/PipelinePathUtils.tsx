import React from 'react';
import {Link, useHistory} from 'react-router-dom';

import {Mono} from '../ui/Text';

export interface ExplorerPath {
  pipelineName: string;
  snapshotId?: string;
  solidsQuery: string;
  pathSolids: string[];
}

export function explorerPathToString(path: ExplorerPath) {
  const root = [
    path.pipelineName,
    path.snapshotId ? `@${path.snapshotId}` : ``,
    path.solidsQuery ? `~${path.solidsQuery}` : ``,
  ].join('');

  return `${root}/${path.pathSolids.join('/')}`;
}

export function explorerPathFromString(path: string): ExplorerPath {
  const rootAndSolids = path.split('/');
  const root = rootAndSolids[0];
  const pathSolids = rootAndSolids.length === 1 ? [''] : rootAndSolids.slice(1);

  const match = /^([^:@~]+)@?([^:~]+)?~?(.*)$/.exec(root);
  const [, pipelineName, snapshotId, solidsQuery] = [...(match || []), '', '', ''];

  return {
    pipelineName,
    snapshotId,
    solidsQuery,
    pathSolids,
  };
}

export function useStripSnapshotFromPath(params: {pipelinePath: string}) {
  const history = useHistory();
  const {pipelinePath} = params;

  React.useEffect(() => {
    const {snapshotId, ...rest} = explorerPathFromString(pipelinePath);
    if (!snapshotId) {
      return;
    }
    history.replace({
      pathname: history.location.pathname.replace(
        new RegExp(`/${pipelinePath}/?`),
        `/${explorerPathToString(rest)}`,
      ),
    });
  }, [history, pipelinePath]);
}

export const PipelineSnapshotLink: React.FC<{
  pipelineName: string;
  snapshotId: string;
  size: 'small' | 'normal';
}> = (props) => {
  const snapshotLink = `/instance/snapshots/${explorerPathToString({
    pipelineName: props.pipelineName,
    snapshotId: props.snapshotId,
    solidsQuery: '',
    pathSolids: [],
  })}`;

  return (
    <Mono style={{fontSize: props.size === 'small' ? '14px' : '16px'}}>
      <Link to={snapshotLink}>{props.snapshotId.slice(0, 8)}</Link>
    </Mono>
  );
};
