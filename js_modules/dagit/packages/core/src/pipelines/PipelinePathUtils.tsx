import React from 'react';
import {Link, useHistory, useRouteMatch} from 'react-router-dom';

import {Mono} from '../ui/Text';
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

export function useEnforceModeInPipelinePath() {
  const {options} = useRepositoryOptions();
  const history = useHistory();

  const match = useRouteMatch<{repoPath: string; pipelinePath: string}>([
    '/workspace/:repoPath/pipelines/:pipelinePath',
    '/workspace/:repoPath/jobs/:pipelinePath',
  ]);

  const pipelinePath = match?.params.pipelinePath;
  const repoPath = match?.params.repoPath;
  const urlMatch = match?.url;

  React.useEffect(() => {
    if (!pipelinePath || !repoPath || !urlMatch) {
      return;
    }
    const repoAddress = repoAddressFromPath(repoPath);
    const path = explorerPathFromString(pipelinePath);
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
      urlMatch.replace(
        new RegExp(`/${pipelinePath}/?`),
        `/${explorerPathToString({...path, pipelineMode: mode})}`,
      ),
    );
  }, [history, pipelinePath, repoPath, urlMatch, options]);
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
    <Mono>
      <Link to={snapshotLink}>{props.snapshotId.slice(0, 8)}</Link>
    </Mono>
  );
};
