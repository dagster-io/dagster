import {Colors, Icon} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {RepoAddress} from '../workspace/types';
import {workspacePipelinePath, workspacePipelinePathGuessRepo} from '../workspace/workspacePath';

import {PipelineSnapshotLink} from './PipelinePathUtils';

interface Props {
  pipelineName: string;
  pipelineHrefContext: 'repo-unknown' | RepoAddress | 'no-link';
  snapshotId?: string | null;
  mode: string;
  showIcon?: boolean;
  fontSize?: number;
}

export const PipelineReference: React.FC<Props> = ({
  pipelineName,
  pipelineHrefContext,
  mode,
  snapshotId,
  showIcon,
  fontSize,
}) => {
  const {flagPipelineModeTuples} = useFeatureFlags();

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
    <span style={{fontSize: fontSize}}>
      {showIcon && (
        <Icon
          color={Colors.GRAY2}
          icon={flagPipelineModeTuples ? 'send-to-graph' : 'diagram-tree'}
          iconSize={Math.floor((fontSize || 16) * 0.8)}
          style={{position: 'relative', top: -2, paddingRight: 5}}
        />
      )}
      {pipeline}
      {snapshotId && ' @ '}
      {snapshotId && (
        <PipelineSnapshotLink
          snapshotId={snapshotId}
          pipelineName={pipelineName}
          pipelineMode={mode}
        />
      )}
    </span>
  );
};
