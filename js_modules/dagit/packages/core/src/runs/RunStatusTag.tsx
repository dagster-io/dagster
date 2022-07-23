import {Box, Popover, Tag} from '@dagster-io/ui';
import * as React from 'react';

import {assertUnreachable} from '../app/Util';
import {RunStatus} from '../types/globalTypes';

import {RunStats} from './RunStats';
import {RunStatusIndicator} from './RunStatusDots';

const statusToIntent = (status: RunStatus) => {
  switch (status) {
    case RunStatus.QUEUED:
    case RunStatus.NOT_STARTED:
    case RunStatus.MANAGED:
    case RunStatus.CANCELING:
      return 'none';
    case RunStatus.SUCCESS:
      return 'success';
    case RunStatus.STARTING:
      return 'none';
    case RunStatus.FAILURE:
    case RunStatus.CANCELED:
      return 'danger';
    case RunStatus.STARTED:
      return 'primary';
    default:
      return assertUnreachable(status);
  }
};

const statusToString = (status: RunStatus) => {
  switch (status) {
    case RunStatus.QUEUED:
      return 'Queued';
    case RunStatus.SUCCESS:
      return 'Success';
    case RunStatus.STARTING:
      return 'Starting';
    case RunStatus.NOT_STARTED:
      return 'Not started';
    case RunStatus.FAILURE:
      return 'Failure';
    case RunStatus.STARTED:
      return 'Started';
    case RunStatus.MANAGED:
      return 'Managed';
    case RunStatus.CANCELING:
      return 'Canceling';
    case RunStatus.CANCELED:
      return 'Canceled';
    default:
      return assertUnreachable(status);
  }
};

export const RunStatusTag = (props: {status: RunStatus}) => {
  const {status} = props;
  return (
    <Tag intent={statusToIntent(status)}>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
        <RunStatusIndicator status={status} size={10} />
        <div>{statusToString(status)}</div>
      </Box>
    </Tag>
  );
};

interface Props {
  runId: string;
  status: RunStatus;
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
