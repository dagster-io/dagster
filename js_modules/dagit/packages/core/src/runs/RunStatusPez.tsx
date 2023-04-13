import {Box, Colors, FontFamily, Mono, Popover} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {RunStatus} from '../graphql/types';
import {StepSummaryForRun} from '../instance/StepSummaryForRun';

import {RunStatusIndicator} from './RunStatusDots';
import {RUN_STATUS_COLORS} from './RunStatusTag';
import {failedStatuses, inProgressStatuses} from './RunStatuses';
import {RunStateSummary, RunTime, titleForRun} from './RunUtils';
import {RunTimeFragment} from './types/RunUtils.types';

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
  jobName: string;
  runs: RunTimeFragment[];
}

export const RunStatusPezList = (props: ListProps) => {
  const {fade, jobName, runs} = props;
  const count = runs.length;
  const countForStep = Math.max(MIN_OPACITY_STEPS, count);
  const step = (MAX_OPACITY - MIN_OPACITY) / countForStep;
  return (
    <Box flex={{direction: 'row', alignItems: 'center', gap: 2}}>
      {runs.map((run, ii) => (
        <Popover
          key={run.id}
          position="top"
          interactionKind="hover"
          content={
            <div>
              <RunStatusOverlay run={run} name={jobName} />
            </div>
          }
          hoverOpenDelay={100}
        >
          <RunStatusPez
            key={run.id}
            runId={run.id}
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
  name: string;
}

export const RunStatusOverlay = ({name, run}: OverlayProps) => {
  return (
    <OverlayContainer>
      <OverlayTitle>{name}</OverlayTitle>
      <RunRow>
        <Box flex={{alignItems: 'center', direction: 'row', gap: 8}}>
          <RunStatusIndicator status={run.status} />
          <Link to={`/runs/${run.id}`}>
            <Mono style={{fontSize: '14px'}}>{titleForRun(run)}</Mono>
          </Link>
        </Box>
        <Box flex={{direction: 'column', gap: 4}} padding={{top: 2}}>
          <RunTime run={run} />
          <RunStateSummary run={run} />
        </Box>
      </RunRow>
      {failedStatuses.has(run.status) || inProgressStatuses.has(run.status) ? (
        <SummaryContainer>
          <StepSummaryForRun runId={run.id} />
        </SummaryContainer>
      ) : null}
    </OverlayContainer>
  );
};

const OverlayContainer = styled.div`
  padding: 4px;
  font-size: 12px;
  width: 220px;
`;

const OverlayTitle = styled.div`
  padding: 8px;
  box-shadow: inset 0 -1px ${Colors.KeylineGray};
  font-family: ${FontFamily.default};
  font-size: 14px;
  font-weight: 500;
  color: ${Colors.Dark};
  max-width: 100%;
  text-overflow: ellipsis;
  overflow: hidden;
  min-width: 0px;
`;

const RunRow = styled.div`
  padding: 8px;
  font-size: 12px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
`;

const SummaryContainer = styled.div`
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 4px 8px 8px;

  :empty {
    display: none;
  }
`;

const Pez = styled.div<{$color: string; $opacity: number}>`
  background-color: ${({$color}) => $color};
  border-radius: 2px;
  height: 16px;
  opacity: ${({$opacity}) => $opacity};
  width: 8px;
`;
