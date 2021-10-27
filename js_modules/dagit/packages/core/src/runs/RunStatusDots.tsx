import * as React from 'react';
import styled, {css, keyframes} from 'styled-components/macro';

import {RunStatus} from '../types/globalTypes';
import {ColorsWIP} from '../ui/Colors';
import {Popover} from '../ui/Popover';
import {Spinner} from '../ui/Spinner';

import {RunStats} from './RunStats';
import {inProgressStatuses, queuedStatuses} from './RunStatuses';

const RUN_STATUS_COLORS = {
  QUEUED: ColorsWIP.Blue200,
  NOT_STARTED: ColorsWIP.Gray600,
  STARTING: ColorsWIP.Gray400,
  MANAGED: ColorsWIP.Gray400,
  STARTED: ColorsWIP.Blue500,
  SUCCESS: ColorsWIP.Green500,
  FAILURE: ColorsWIP.Red500,
  CANCELING: ColorsWIP.Red500,
  CANCELED: ColorsWIP.Red500,
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
  status: RunStatus;
  size?: number;
}

export const RunStatusIndicator: React.FC<RunStatusProps> = React.memo(({status, size}) => {
  if (status === 'STARTED') {
    return <Spinner purpose="caption-text" />;
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
  status: RunStatus;
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
