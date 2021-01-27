import {Popover, Colors} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {RunStats} from 'src/runs/RunStats';
import {Spinner} from 'src/ui/Spinner';

export type IRunStatus =
  | 'SUCCESS'
  | 'QUEUED'
  | 'NOT_STARTED'
  | 'FAILURE'
  | 'STARTED'
  | 'MANAGED'
  | 'STARTING'
  | 'CANCELING'
  | 'CANCELED';

const RUN_STATUS_COLORS = {
  QUEUED: Colors.BLUE1,
  NOT_STARTED: Colors.GRAY1,
  STARTING: Colors.GRAY3,
  MANAGED: Colors.GRAY3,
  STARTED: Colors.GRAY3,
  SUCCESS: Colors.GREEN2,
  FAILURE: Colors.RED3,
  CANCELING: Colors.RED1,
  CANCELED: Colors.RED3,
};

const RUN_STATUS_HOVER_COLORS = {
  QUEUED: Colors.BLUE3,
  NOT_STARTED: Colors.GRAY3,
  STARTING: Colors.GRAY5,
  MANAGED: Colors.GRAY3,
  STARTED: Colors.GRAY5,
  SUCCESS: Colors.GREEN4,
  FAILURE: Colors.RED5,
  CANCELING: Colors.RED3,
  CANCELED: Colors.RED5,
};
export const RunStatusWithStats: React.FunctionComponent<
  RunStatusProps & {
    runId: string;
  }
> = React.memo(({runId, ...rest}) => (
  <Popover
    position={'bottom'}
    interactionKind={'hover'}
    content={<RunStats runId={runId} />}
    hoverOpenDelay={100}
  >
    <div style={{padding: 1}}>
      <RunStatus {...rest} />
    </div>
  </Popover>
));

interface RunStatusProps {
  status: IRunStatus;
  size?: number;
}

export const RunStatus: React.FC<RunStatusProps> = React.memo(({status, size}) => {
  if (status === 'STARTED') {
    return (
      <div style={{display: 'inline-block'}}>
        <Spinner purpose="body-text" />
      </div>
    );
  }
  return <RunStatusDot status={status} size={size || 11} />;
});

export const RunStatusDot = styled.div<{
  status: IRunStatus;
  size: number;
}>`
  display: inline-block;
  width: ${({size}) => size}px;
  height: ${({size}) => size}px;
  border-radius: ${({size}) => size / 2}px;
  align-self: center;
  transition: background 200ms linear;
  background: ${({status}) => RUN_STATUS_COLORS[status]};
  &:hover {
    background: ${({status}) => RUN_STATUS_HOVER_COLORS[status]};
  }
`;
