import {gql} from '@apollo/client';
import {Colors, Group, Mono} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {LastRunSummary} from '../instance/LastRunSummary';
import {RunStatusIndicator} from '../runs/RunStatusDots';
import {RUN_TIME_FRAGMENT, titleForRun} from '../runs/RunUtils';

import {TICK_TAG_FRAGMENT} from './InstigationTick';
import {InstigationStateFragment, RunStatusFragment} from './types/InstigationUtils.types';

export const InstigatedRunStatus = ({
  instigationState,
}: {
  instigationState: InstigationStateFragment;
}) => {
  const [instigationRun] = instigationState.runs;
  if (!instigationRun) {
    return <span style={{color: Colors.Gray300}}>None</span>;
  }
  return <LastRunSummary run={instigationRun} name={instigationState.name} />;
};

export const RunStatusLink = ({run}: {run: RunStatusFragment}) => (
  <Group direction="row" spacing={4} alignItems="center">
    <RunStatusIndicator status={run.status} />
    <Link to={`/runs/${run.id}`} target="_blank" rel="noreferrer">
      <Mono>{titleForRun({id: run.id})}</Mono>
    </Link>
  </Group>
);

export const RUN_STATUS_FRAGMENT = gql`
  fragment RunStatusFragment on Run {
    id
    status
  }
`;

export const INSTIGATION_STATE_FRAGMENT = gql`
  fragment InstigationStateFragment on InstigationState {
    id
    selectorId
    name
    instigationType
    status
    hasStartPermission
    hasStopPermission
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

  ${RUN_STATUS_FRAGMENT}
  ${RUN_TIME_FRAGMENT}
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
    color: ${Colors.Gray500};
  }
`;

export const DYNAMIC_PARTITIONS_REQUEST_RESULT_FRAGMENT = gql`
  fragment DynamicPartitionsRequestResultFragment on DynamicPartitionsRequestResult {
    partitionsDefName
    partitionKeys
    skippedPartitionKeys
    type
  }
`;

export const HISTORY_TICK_FRAGMENT = gql`
  fragment HistoryTick on InstigationTick {
    id
    status
    timestamp
    endTimestamp
    cursor
    instigationType
    skipReason
    runIds
    runs {
      id
      status
      ...RunStatusFragment
    }
    originRunIds
    error {
      ...PythonErrorFragment
    }
    logKey
    ...TickTagFragment
    dynamicPartitionsRequestResults {
      ...DynamicPartitionsRequestResultFragment
    }
  }
  ${RUN_STATUS_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
  ${TICK_TAG_FRAGMENT}
  ${DYNAMIC_PARTITIONS_REQUEST_RESULT_FRAGMENT}
`;
