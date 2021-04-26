import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {PipelineSnapshotLink} from './PipelinePathUtils';

interface Props {
  pipelineName: string;
  pipelineHrefContext: 'repo-unknown' | RepoAddress | 'no-link';
  snapshotId?: string | null;
  mode: string;
}

export const PipelineReference: React.FC<Props> = ({
  pipelineName,
  pipelineHrefContext,
  mode,
  snapshotId,
}) => {
  const pipeline =
    pipelineHrefContext === 'repo-unknown' ? (
      <Link to={`/workspace/pipelines/${pipelineName}`}>{pipelineName}</Link>
    ) : pipelineHrefContext === 'no-link' ? (
      pipelineName
    ) : (
      <Link to={workspacePathFromAddress(pipelineHrefContext, `/pipelines/${pipelineName}/`)}>
        {pipelineName}
      </Link>
    );

  return (
    <>
      {pipeline}
      {snapshotId && ' @ '}
      {snapshotId && <PipelineSnapshotLink snapshotId={snapshotId} pipelineName={pipelineName} />}
      {mode === 'default' ? null : <span style={{color: Colors.GRAY3}}>{`: ${mode}`}</span>}
    </>
  );
};
