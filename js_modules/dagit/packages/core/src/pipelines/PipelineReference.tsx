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
  isJob: boolean;
  snapshotId?: string | null;
  showIcon?: boolean;
  size?: 'small' | 'normal';
}

export const PipelineReference: React.FC<Props> = ({
  pipelineName,
  pipelineHrefContext,
  isJob,
  snapshotId,
  showIcon,
  size = 'normal',
}) => {
  const pipeline =
    pipelineHrefContext === 'repo-unknown' ? (
      <Link to={workspacePipelinePathGuessRepo(pipelineName, isJob)}>{pipelineName}</Link>
    ) : pipelineHrefContext === 'no-link' ? (
      <>{pipelineName}</>
    ) : (
      <Link
        to={workspacePipelinePath({
          repoName: pipelineHrefContext.name,
          repoLocation: pipelineHrefContext.location,
          pipelineName,
          isJob,
        })}
      >
        {pipelineName}
      </Link>
    );

  return (
    <Box flex={{direction: 'row', alignItems: 'center', display: 'inline-flex'}}>
      {showIcon && (
        <Box margin={{right: 8}}>
          <IconWIP color={ColorsWIP.Gray400} name="job" />
        </Box>
      )}
      <span>
        {pipeline}
        {snapshotId && ' @ '}
        {snapshotId && (
          <PipelineSnapshotLink snapshotId={snapshotId} pipelineName={pipelineName} size={size} />
        )}
      </span>
    </Box>
  );
};
