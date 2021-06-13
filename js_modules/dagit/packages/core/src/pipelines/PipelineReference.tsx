import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {RepoAddress} from '../workspace/types';
import {workspacePipelinePath, workspacePipelinePathGuessRepo} from '../workspace/workspacePath';

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
  const modeLabel =
    mode === 'default' ? null : <span style={{color: Colors.GRAY3}}>{`: ${mode}`}</span>;

  const pipeline =
    pipelineHrefContext === 'repo-unknown' ? (
      <Link to={workspacePipelinePathGuessRepo(pipelineName, mode)}>
        {pipelineName}
        {modeLabel}
      </Link>
    ) : pipelineHrefContext === 'no-link' ? (
      <>
        {pipelineName}
        {modeLabel}
      </>
    ) : (
      <Link
        to={workspacePipelinePath(
          pipelineHrefContext.name,
          pipelineHrefContext.location,
          pipelineName,
          mode,
        )}
      >
        {pipelineName}
        {modeLabel}
      </Link>
    );

  return (
    <>
      {pipeline}
      {snapshotId && ' @ '}
      {snapshotId && (
        <PipelineSnapshotLink
          snapshotId={snapshotId}
          pipelineName={pipelineName}
          pipelineMode={mode}
        />
      )}
    </>
  );
};
