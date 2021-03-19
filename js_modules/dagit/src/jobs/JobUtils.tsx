import {gql} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {RunStatus} from '../runs/RunStatusDots';
import {titleForRun} from '../runs/RunUtils';
import {Group} from '../ui/Group';
import {FontFamily} from '../ui/styles';
import {REPOSITORY_ORIGIN_FRAGMENT} from '../workspace/RepositoryInformation';

import {TICK_TAG_FRAGMENT} from './JobTick';
import {JobStateFragment} from './types/JobStateFragment';

export const JobRunStatus: React.FC<{
  jobState: JobStateFragment;
}> = ({jobState}) => {
  if (!jobState.runs.length) {
    return <span style={{color: Colors.GRAY4}}>None</span>;
  }
  const run = jobState.runs[0];
  return (
    <Group direction="row" spacing={4} alignItems="center">
      <RunStatus status={run.status} />
      <Link to={`/instance/runs/${run.runId}`} target="_blank" rel="noreferrer">
        <span style={{fontFamily: FontFamily.monospace}}>{titleForRun({runId: run.runId})}</span>
      </Link>
    </Group>
  );
};

export const JOB_STATE_FRAGMENT = gql`
  fragment JobStateFragment on JobState {
    id
    name
    jobType
    status
    repositoryOrigin {
      id
      ...RepositoryOriginFragment
    }
    jobSpecificData {
      ... on SensorJobData {
        lastRunKey
      }
      ... on ScheduleJobData {
        cronSchedule
      }
    }
    runs(limit: 1) {
      id
      runId
      status
    }
    status
    ticks(limit: 1) {
      id
      ...TickTagFragment
    }
    runningCount
  }
  ${REPOSITORY_ORIGIN_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
  ${TICK_TAG_FRAGMENT}
`;

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
    color: ${Colors.GRAY2};
  }
`;
