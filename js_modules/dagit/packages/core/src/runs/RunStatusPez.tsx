import {Box, ColorsWIP, FontFamily, Mono, Popover} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {SectionHeader} from '../pipelines/SidebarComponents';
import {RunStatus} from '../types/globalTypes';

import {RunStatusIndicator} from './RunStatusDots';
import {RunTime, titleForRun} from './RunUtils';
import {RunTimeFragment} from './types/RunTimeFragment';

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
const MIN_OPACITY_STEPS = 3;

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
  repoAddress: string;
  runs: RunTimeFragment[];
}

export const RunStatusPezList = (props: ListProps) => {
  const {fade, runs} = props;
  const count = runs.length;
  const countForStep = Math.max(MIN_OPACITY_STEPS, count);
  const step = (MAX_OPACITY - MIN_OPACITY) / countForStep;
  return (
    <Box flex={{direction: 'row', alignItems: 'center', gap: 2}}>
      {runs.map((run, ii) => (
        <Popover
          key={run.runId}
          position="bottom"
          interactionKind="hover"
          content={
            <div>
              <RunStatusOverlay run={run} repoAddr={props.repoAddress} />
            </div>
          }
          hoverOpenDelay={100}
        >
          <RunStatusPez
            key={run.runId}
            runId={run.runId}
            status={run.status}
            opacity={fade ? MAX_OPACITY - (count - ii - 1) * step : 1.0}
          />
        </Popover>
      ))}
    </Box>
  );
};

interface OverlayProps {
  run: RunTimeFragment;
  repoAddr: string;
}

const RunStatusOverlay = (props: OverlayProps) => {
  return (
    <OverlayContainer>
      <OverlayTitle>{props.repoAddr}</OverlayTitle>
      <RunRow>
        <RunStatusIndicator status={props.run.status} />
        <Link to={`/instance/runs/${props.run.runId}`}>
          <Mono>{titleForRun(props.run)}</Mono>
        </Link>
        <HorizontalSpace />
        <RunTime run={props.run} />
      </RunRow>
    </OverlayContainer>
  );
};

const OverlayContainer = styled.div`
  padding: 4px;
  font-size: 12px;
  width: 250px;
`;

const HorizontalSpace = styled.div`
  flex: 1;
`;

const OverlayTitle = styled(SectionHeader)`
  padding: 8px;
  box-shadow: inset 0 -1px ${ColorsWIP.KeylineGray};
  max-width: 100%;
  text-overflow: ellipsis;
  overflow: hidden;
  min-width: 0px;
`;

const RunRow = styled.div`
  align-items: center;
  padding: 8px;
  font-family: ${FontFamily.monospace};
  font-size: 14px;
  line-height: 20px;
  display: flex;
  gap: 8px;
`;

const Pez = styled.div<{$color: string; $opacity: number}>`
  background-color: ${({$color}) => $color};
  border-radius: 2px;
  height: 16px;
  opacity: ${({$opacity}) => $opacity};
  width: 8px;
`;
