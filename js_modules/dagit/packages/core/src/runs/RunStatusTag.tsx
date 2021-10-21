import * as React from 'react';

import {assertUnreachable} from '../app/Util';
import {PipelineRunStatus} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {Popover} from '../ui/Popover';
import {TagWIP} from '../ui/TagWIP';

import {RunStats} from './RunStats';
import {RunStatusIndicator} from './RunStatusDots';

const statusToIntent = (status: PipelineRunStatus) => {
  switch (status) {
    case PipelineRunStatus.QUEUED:
    case PipelineRunStatus.NOT_STARTED:
    case PipelineRunStatus.MANAGED:
    case PipelineRunStatus.CANCELING:
      return 'none';
    case PipelineRunStatus.SUCCESS:
      return 'success';
    case PipelineRunStatus.STARTING:
      return 'none';
    case PipelineRunStatus.FAILURE:
    case PipelineRunStatus.CANCELED:
      return 'danger';
    case PipelineRunStatus.STARTED:
      return 'primary';
    default:
      return assertUnreachable(status);
  }
};

const statusToString = (status: PipelineRunStatus) => {
  switch (status) {
    case PipelineRunStatus.QUEUED:
      return 'Queued';
    case PipelineRunStatus.SUCCESS:
      return 'Success';
    case PipelineRunStatus.STARTING:
      return 'Starting';
    case PipelineRunStatus.NOT_STARTED:
      return 'Not started';
    case PipelineRunStatus.FAILURE:
      return 'Failure';
    case PipelineRunStatus.STARTED:
      return 'Started';
    case PipelineRunStatus.MANAGED:
      return 'Managed';
    case PipelineRunStatus.CANCELING:
      return 'Canceling';
    case PipelineRunStatus.CANCELED:
      return 'Canceled';
    default:
      return assertUnreachable(status);
  }
};

export const RunStatusTag = (props: {status: PipelineRunStatus}) => {
  const {status} = props;
  return (
    <TagWIP intent={statusToIntent(status)}>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
        <RunStatusIndicator status={status} size={10} />
        <div>{statusToString(status)}</div>
      </Box>
    </TagWIP>
  );
};

interface Props {
  runId: string;
  status: PipelineRunStatus;
}

export const RunStatusTagWithStats = (props: Props) => {
  const {runId, status} = props;
  return (
    <Popover
      position="bottom-left"
      interactionKind="hover"
      content={<RunStats runId={runId} />}
      hoverOpenDelay={100}
      usePortal
    >
      <RunStatusTag status={status} />
    </Popover>
  );
};
