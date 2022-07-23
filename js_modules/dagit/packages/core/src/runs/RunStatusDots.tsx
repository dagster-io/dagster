import {Colors, Popover, Spinner} from '@dagster-io/ui';
import * as React from 'react';
import styled, {css, keyframes} from 'styled-components/macro';

import {RunStatus} from '../types/globalTypes';

import {RunStats} from './RunStats';
import {inProgressStatuses, queuedStatuses} from './RunStatuses';

const RUN_STATUS_COLORS = {
  QUEUED: Colors.Blue200,
  NOT_STARTED: Colors.Gray600,
  STARTING: Colors.Gray400,
  MANAGED: Colors.Gray400,
  STARTED: Colors.Blue500,
  SUCCESS: Colors.Green500,
  FAILURE: Colors.Red500,
  CANCELING: Colors.Red500,
  CANCELED: Colors.Red500,

  // Not technically a RunStatus, but useful.
  SCHEDULED: Colors.Blue200,
};

export const RunStatusWithStats: React.FC<RunStatusProps & {runId: string}> = React.memo(
  ({runId, ...rest}) => (
    <Popover
      position="bottom"
      interactionKind="hover"
      content={<RunStats runId={runId} />}
      hoverOpenDelay={100}
    >
      <RunStatusIndicator {...rest} />
    </Popover>
  ),
);

interface RunStatusProps {
  status: RunStatus | 'SCHEDULED';
  size?: number;
}

export const RunStatusIndicator: React.FC<RunStatusProps> = React.memo(({status, size}) => {
  if (status === 'STARTED') {
    return <Spinner purpose="caption-text" />;
  }
  if (status === 'SCHEDULED') {
    return <RunStatusDot status={status} size={size || 12} />;
  }
  return (
    <RunStatusDot
      status={status}
      size={size || 12}
      pulse={inProgressStatuses.has(status) || queuedStatuses.has(status)}
    />
  );
});

const pulseAnimation = keyframes`
  0% {
    filter: brightness(1);
  }

  50% {
    filter: brightness(0.7);
  }

  100% {
    filter: brightness(1);
  }
`;

export const RunStatusDot = styled.div<{
  status: RunStatus | 'SCHEDULED';
  size: number;
  pulse?: boolean;
}>`
  width: ${({size}) => size}px;
  height: ${({size}) => size}px;
  border-radius: ${({size}) => size / 2}px;
  transition: filter 200ms linear;
  ${({pulse}) =>
    pulse
      ? css`
          animation: ${pulseAnimation} 2s infinite;
        `
      : null}

  background: ${({status}) => RUN_STATUS_COLORS[status]};
  &:hover {
    animation: none;
    filter: brightness(0.7);
  }
`;
