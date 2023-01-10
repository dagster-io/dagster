import {Colors, Group, Mono} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {graphql} from '../graphql';
import {InstigationStateFragmentFragment, RunStatusFragmentFragment} from '../graphql/graphql';
import {LastRunSummary} from '../instance/LastRunSummary';
import {RunStatusIndicator} from '../runs/RunStatusDots';
import {titleForRun} from '../runs/RunUtils';

export const InstigatedRunStatus: React.FC<{
  instigationState: InstigationStateFragmentFragment;
}> = ({instigationState}) => {
  if (!instigationState.runs.length) {
    return <span style={{color: Colors.Gray300}}>None</span>;
  }
  return <LastRunSummary run={instigationState.runs[0]} name={instigationState.name} />;
};

export const RunStatusLink: React.FC<{run: RunStatusFragmentFragment}> = ({run}) => (
  <Group direction="row" spacing={4} alignItems="center">
    <RunStatusIndicator status={run.status} />
    <Link to={`/runs/${run.runId}`} target="_blank" rel="noreferrer">
      <Mono>{titleForRun({runId: run.runId})}</Mono>
    </Link>
  </Group>
);

export const RUN_STATUS_FRAGMENT = graphql(`
  fragment RunStatusFragment on Run {
    id
    runId
    status
  }
`);

export const INSTIGATION_STATE_FRAGMENT = graphql(`
  fragment InstigationStateFragment on InstigationState {
    id
    selectorId
    name
    instigationType
    status
    repositoryName
    repositoryLocationName
    typeSpecificData {
      ... on SensorData {
        lastRunKey
        lastCursor
      }
      ... on ScheduleData {
        cronSchedule
      }
    }
    runs(limit: 1) {
      id
      ...RunStatusFragment
      ...RunTimeFragment
    }
    status
    ticks(limit: 1) {
      id
      cursor
      ...TickTagFragment
    }
    runningCount
  }
`);

export const StatusTable = styled.table`
  font-size: 13px;
  border-spacing: 0;

  &&&&& tr {
    box-shadow: none;
  }

  &&&&& tbody > tr > td {
    background: transparent;
    box-shadow: none !important;
    padding: 1px 0;
  }

  &&&&& tbody > tr > td:first-child {
    color: ${Colors.Gray500};
  }
`;
