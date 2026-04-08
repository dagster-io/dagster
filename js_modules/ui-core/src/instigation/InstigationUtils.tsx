import {Box, Colors, Mono} from '@dagster-io/ui-components';
import clsx from 'clsx';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {TICK_TAG_FRAGMENT} from './InstigationTick';
import {gql} from '../apollo-client';
import {InstigationStateFragment, RunStatusFragment} from './types/InstigationUtils.types';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {LastRunSummary} from '../instance/LastRunSummary';
import {RunStatusIndicator} from '../runs/RunStatusDots';
import {RUN_TIME_FRAGMENT, titleForRun} from '../runs/RunUtils';
import styles from './css/InstigationUtils.module.css';

export const InstigatedRunStatus = ({
  instigationState,
}: {
  instigationState: InstigationStateFragment;
}) => {
  const [instigationRun] = instigationState.runs;
  if (!instigationRun) {
    return <span style={{color: Colors.textLight()}}>None</span>;
  }
  return <LastRunSummary run={instigationRun} name={instigationState.name} />;
};

export const RunStatusLink = ({run}: {run: RunStatusFragment}) => (
  <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
    <RunStatusIndicator status={run.status} />
    <Link to={`/runs/${run.id}`} target="_blank" rel="noreferrer">
      <Mono>{titleForRun({id: run.id})}</Mono>
    </Link>
  </Box>
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
    tickId
    status
    timestamp
    endTimestamp
    cursor
    instigationType
    skipReason
    requestedAssetMaterializationCount
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

export const StatusTable = React.forwardRef<
  HTMLTableElement,
  React.ComponentPropsWithoutRef<'table'>
>((props, ref) => {
  return <table {...props} ref={ref} className={clsx(styles.statusTable, props.className)} />;
});
