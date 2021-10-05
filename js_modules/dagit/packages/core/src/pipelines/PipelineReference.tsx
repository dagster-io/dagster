import * as React from 'react';
import {Link} from 'react-router-dom';

import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {IconWIP} from '../ui/Icon';
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
}) => {
  const modeLabel =
    mode === 'default' ? null : <span style={{color: ColorsWIP.Gray400}}>{`: ${mode}`}</span>;

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
    <Box flex={{direction: 'row', alignItems: 'center'}}>
      {showIcon && (
        <Box margin={{right: 8}}>
          <IconWIP color={ColorsWIP.Gray400} name={'job'} />
        </Box>
      )}
      <span>
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
    </Box>
  );
};
