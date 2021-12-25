import * as React from 'react';
import styled from 'styled-components/macro';

import {RunStatus} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {Popover} from '../ui/Popover';

import {RunStats} from './RunStats';

const RUN_STATUS_COLORS = {
  QUEUED: ColorsWIP.Blue500,
  NOT_STARTED: ColorsWIP.Blue500,
  STARTING: ColorsWIP.Blue500,
  MANAGED: ColorsWIP.Blue500,
  STARTED: ColorsWIP.Blue500,
  SUCCESS: ColorsWIP.Green500,
  FAILURE: ColorsWIP.Red500,
  CANCELING: ColorsWIP.Red500,
  CANCELED: ColorsWIP.Red500,
};

const MIN_OPACITY = 0.2;
const MAX_OPACITY = 1.0;

interface Props {
  opacity?: number;
  runId: string;
  status: RunStatus;
}

export const RunStatusPez = (props: Props) => {
  const {status, opacity = MAX_OPACITY} = props;
  const color = RUN_STATUS_COLORS[status];

  return <Pez $color={color} $opacity={opacity} />;
};

interface ListProps {
  fade: boolean;
  runs: {runId: string; status: RunStatus}[];
}

export const RunStatusPezList = (props: ListProps) => {
  const {fade, runs} = props;
  const step = (MAX_OPACITY - MIN_OPACITY) / (runs.length || 1);
  return (
    <Box flex={{direction: 'row', alignItems: 'center', gap: 2}}>
      {runs.map((run, ii) => (
        <Popover
          key={run.runId}
          position="bottom"
          interactionKind="hover"
          content={<RunStats runId={run.runId} />}
          hoverOpenDelay={100}
        >
          <RunStatusPez
            key={run.runId}
            runId={run.runId}
            status={run.status}
            opacity={fade ? MIN_OPACITY + ii * step : 1.0}
          />
        </Popover>
      ))}
    </Box>
  );
};

const Pez = styled.div<{$color: string; $opacity: number}>`
  background-color: ${({$color}) => $color};
  border-radius: 2px;
  height: 16px;
  opacity: ${({$opacity}) => $opacity};
  width: 8px;
`;
