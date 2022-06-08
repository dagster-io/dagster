import {Mono} from '@dagster-io/ui';
import React from 'react';
import {Link, useHistory} from 'react-router-dom';

import {__ASSET_JOB_PREFIX} from '../asset-graph/Utils';

export interface ExplorerPath {
  pipelineName: string;
  snapshotId?: string;
  opsQuery: string;
  explodeComposites?: boolean;
  opNames: string[];
}

export function explorerPathToString(path: ExplorerPath) {
  const root = [
    path.pipelineName,
    path.snapshotId ? `@${path.snapshotId}` : ``,
    path.opsQuery
      ? `~${path.explodeComposites ? '!' : ''}${encodeURIComponent(path.opsQuery)}`
      : ``,
  ].join('');

  return `${root}/${path.opNames.map(encodeURIComponent).join('/')}`;
}

export function explorerPathFromString(path: string): ExplorerPath {
  const rootAndOps = path.split('/');
  const root = rootAndOps[0];
  const opNames = rootAndOps.length === 1 ? [''] : rootAndOps.slice(1);

  const match = /^([^@~]+)@?([^~]+)?~?(!)?(.*)$/.exec(root);
  const [, pipelineName, snapshotId, explodeComposites, opsQuery] = [
    ...(match || []),
    '',
    '',
    '',
    '',
  ];

  return {
    pipelineName,
    snapshotId,
    opsQuery: decodeURIComponent(opsQuery),
    explodeComposites: explodeComposites === '!',
    opNames: opNames.map(decodeURIComponent),
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
    opsQuery: '',
    opNames: [],
  })}`;

  return (
    <Mono style={{fontSize: props.size === 'small' ? '14px' : '16px'}}>
      <Link to={snapshotLink}>{props.snapshotId.slice(0, 8)}</Link>
    </Mono>
  );
};
