import {Mono} from '@dagster-io/ui';
import React from 'react';
import {Link, useHistory} from 'react-router-dom';

import {__ASSET_GROUP} from '../workspace/asset-graph/Utils';

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
    path.opsQuery ? `~${path.explodeComposites ? '!' : ''}${path.opsQuery}` : ``,
  ].join('');

  return `${root}/${path.opNames.join('/')}`;
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
    opsQuery,
    explodeComposites: explodeComposites === '!',
    opNames,
  };
}

export function instanceAssetsExplorerPathFromString(path: string): ExplorerPath {
  // This is a bit of a hack, but our explorer path needs a job name and we'd like
  // to continue sharing the parsing/stringifying logic from the job graph UI
  return explorerPathFromString(__ASSET_GROUP + path || '/');
}

export function instanceAssetsExplorerPathToURL(path: Omit<ExplorerPath, 'pipelineName'>) {
  return (
    '/instance/asset-graph' +
    explorerPathToString({...path, pipelineName: __ASSET_GROUP}).replace(__ASSET_GROUP, '')
  );
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
