import {Box, ColorsWIP, IconWIP} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {RepoAddress} from '../workspace/types';
import {workspacePipelinePath, workspacePipelinePathGuessRepo} from '../workspace/workspacePath';

import {PipelineSnapshotLink} from './PipelinePathUtils';

export interface Props {
  pipelineName: string;
  pipelineHrefContext: 'repo-unknown' | RepoAddress | 'no-link';
  isJob: boolean;
  snapshotId?: string | null;
  showIcon?: boolean;
  size?: 'small' | 'normal';
}

const TRUNCATION_THRESHOLD = 40;
const TRUNCATION_BUFFER = 5;

export const PipelineReference: React.FC<Props> = ({
  pipelineName,
  pipelineHrefContext,
  isJob,
  snapshotId,
  showIcon,
  size = 'normal',
}) => {
  const truncatedName =
    pipelineName.length > TRUNCATION_THRESHOLD
      ? `${pipelineName.slice(0, TRUNCATION_THRESHOLD - TRUNCATION_BUFFER)}…`
      : pipelineName;

  const pipeline =
    pipelineHrefContext === 'repo-unknown' ? (
      <Link to={workspacePipelinePathGuessRepo(pipelineName, isJob)}>{truncatedName}</Link>
    ) : pipelineHrefContext === 'no-link' ? (
      <>{truncatedName}</>
    ) : (
      <Link
        to={workspacePipelinePath({
          repoName: pipelineHrefContext.name,
          repoLocation: pipelineHrefContext.location,
          pipelineName,
          isJob,
        })}
      >
        {truncatedName}
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
