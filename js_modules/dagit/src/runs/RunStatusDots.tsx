import {Spinner, Popover, Colors} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {RunStats} from 'src/runs/RunStats';

export type IRunStatus = 'SUCCESS' | 'NOT_STARTED' | 'FAILURE' | 'STARTED' | 'MANAGED';

export const RUN_STATUS_COLORS = {
  NOT_STARTED: Colors.GRAY1,
  MANAGED: Colors.GRAY3,
  STARTED: Colors.GRAY3,
  SUCCESS: Colors.GREEN2,
  FAILURE: Colors.RED3,
};

export const RUN_STATUS_HOVER_COLORS = {
  NOT_STARTED: Colors.GRAY3,
  MANAGED: Colors.GRAY3,
  STARTED: Colors.GRAY5,
  SUCCESS: Colors.GREEN4,
  FAILURE: Colors.RED5,
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

export const RunStatus: React.FunctionComponent<RunStatusProps> = React.memo(({status, size}) => {
  if (status === 'STARTED') {
    return (
      <div style={{display: 'inline-block'}}>
        <Spinner size={size || 11} />
      </div>
    );
  }
  return <RunStatusDot status={status} size={size || 11} />;
});

// eslint-disable-next-line no-unexpected-multiline
const RunStatusDot = styled.div<{
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
