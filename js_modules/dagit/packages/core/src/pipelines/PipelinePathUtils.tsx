import React from 'react';
import {Link, useHistory, useRouteMatch} from 'react-router-dom';

import {FontFamily} from '../ui/styles';
import {useRepositoryOptions} from '../workspace/WorkspaceContext';
import {repoAddressFromPath} from '../workspace/repoAddressFromPath';

export interface PipelineExplorerPath {
  pipelineName: string;
  pipelineMode: string;
  snapshotId?: string;
  solidsQuery: string;
  pathSolids: string[];
}

export function explorerPathToString(path: PipelineExplorerPath) {
  const root = [
    path.pipelineName,
    path.snapshotId ? `@${path.snapshotId}` : ``,
    ':',
    path.pipelineMode,
    path.solidsQuery ? `~${path.solidsQuery}` : ``,
  ].join('');

  return `${root}/${path.pathSolids.join('/')}`;
}

export function explorerPathFromString(path: string) {
  const [root, ...pathSolids] = path.split('/');
  const match = /^([^:@~]+)@?([^:~]+)?:?([^:~]+)?~?(.*)$/.exec(root);
  const [, pipelineName, snapshotId, pipelineMode, solidsQuery] = [
    ...(match || []),
    '',
    '',
    '',
    '',
  ];

  return {
    pipelineName,
    pipelineMode,
    snapshotId,
    solidsQuery,
    pathSolids,
  };
}

export function useStripSnapshotFromPath(params: {pipelinePath: string}) {
  const history = useHistory();

  React.useEffect(() => {
    const path = explorerPathFromString(params.pipelinePath);
    if (!path.snapshotId) {
      return;
    }
    history.replace({
      pathname: history.location.pathname.replace(
        `/${params.pipelinePath}/`,
        `/${explorerPathToString({...path, snapshotId: undefined})}`,
      ),
    });
  }, [history, params]);
}

export function useEnforceModeInPipelinePath() {
  const {options} = useRepositoryOptions();
  const history = useHistory();

  const match = useRouteMatch<{repoPath: string; pipelinePath: string}>(
    '/workspace/:repoPath/pipelines/:pipelinePath',
  );

  React.useEffect(() => {
    if (!match) {
      return;
    }
    const repoAddress = repoAddressFromPath(match.params.repoPath);
    const path = explorerPathFromString(match.params.pipelinePath);
    if (!repoAddress || path.pipelineMode) {
      return;
    }

    const repo = options.find(
      (o) =>
        o.repository.name === repoAddress.name &&
        o.repositoryLocation.name === repoAddress.location,
    );
    const mode = repo?.repository.pipelines.find((p) => p.name === path.pipelineName)?.modes[0]
      .name;

    if (!mode) {
      return;
    }
    history.replace(
      match.url.replace(
        `/${match.params.pipelinePath}/`,
        `/${explorerPathToString({...path, pipelineMode: mode})}`,
      ),
    );
  }, [history, match, options]);
}

export const PipelineSnapshotLink: React.FunctionComponent<{
  pipelineName: string;
  pipelineMode: string;
  snapshotId: string;
}> = (props) => {
  const snapshotLink = `/instance/snapshots/${explorerPathToString({
    pipelineName: props.pipelineName,
    pipelineMode: props.pipelineMode,
    snapshotId: props.snapshotId,
    solidsQuery: '',
    pathSolids: [],
  })}`;

  return (
    <span style={{fontFamily: FontFamily.monospace}}>
      <Link to={snapshotLink}>{props.snapshotId.slice(0, 8)}</Link>
    </span>
  );
};
