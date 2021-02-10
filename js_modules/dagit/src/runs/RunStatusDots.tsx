import {Popover, Colors} from '@blueprintjs/core';
import * as React from 'react';
import styled, {css, keyframes} from 'styled-components';

import {RunStats} from 'src/runs/RunStats';
import {inProgressStatuses, queuedStatuses} from 'src/runs/RunStatuses';
import {PipelineRunStatus} from 'src/types/globalTypes';
import {Spinner} from 'src/ui/Spinner';

const RUN_STATUS_COLORS = {
  QUEUED: Colors.BLUE5,
  NOT_STARTED: Colors.GRAY1,
  STARTING: Colors.GRAY3,
  MANAGED: Colors.GRAY3,
  STARTED: Colors.GRAY3,
  SUCCESS: Colors.GREEN4,
  FAILURE: Colors.RED3,
  CANCELING: Colors.RED3,
  CANCELED: Colors.RED3,
};

export const RunStatusWithStats: React.FC<RunStatusProps & {runId: string}> = React.memo(
  ({runId, ...rest}) => (
    <Popover
      position={'bottom'}
      interactionKind={'hover'}
      content={<RunStats runId={runId} />}
      hoverOpenDelay={100}
    >
      <RunStatus {...rest} />
    </Popover>
  ),
);

interface RunStatusProps {
  status: PipelineRunStatus;
  size?: number;
}

export const RunStatus: React.FC<RunStatusProps> = React.memo(({status, size}) => {
  if (status === 'STARTED') {
    return <Spinner purpose="body-text" />;
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
  status: PipelineRunStatus;
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
