import {gql} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import React from 'react';

import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {REPOSITORY_INFO_FRAGMENT, REPOSITORY_ORIGIN_FRAGMENT} from 'src/RepositoryInformation';
import {SCHEDULER_FRAGMENT} from 'src/schedules/SchedulerInfo';
import {SchedulerFragment} from 'src/schedules/types/SchedulerFragment';
import {JOB_STATE_FRAGMENT} from 'src/sensors/SensorFragment';

export const SCHEDULE_STATE_FRAGMENT = gql`
  fragment ScheduleStateFragment on ScheduleState {
    __typename
    id
    scheduleOriginId
    repositoryOrigin {
      ...RepositoryOriginFragment
    }
    repositoryOriginId
    scheduleName
    cronSchedule
    runningScheduleCount
    ticks(limit: 1) {
      tickId
      status
      timestamp
      tickSpecificData {
        __typename
        ... on ScheduleTickSuccessData {
          run {
            id
            pipelineName
            status
            runId
          }
        }
        ... on ScheduleTickFailureData {
          error {
            ...PythonErrorFragment
          }
        }
      }
    }
    runsCount
    runs(limit: 10) {
      id
      runId
      tags {
        key
        value
      }
      pipelineName
      status
    }
    ticksCount
    status
  }

  ${PythonErrorInfo.fragments.PythonErrorFragment}
  ${REPOSITORY_ORIGIN_FRAGMENT}
`;

export const REPOSITORY_SCHEDULES_FRAGMENT = gql`
  fragment RepositorySchedulesFragment on Repository {
    name
    id
    schedules {
      id
      ...ScheduleFragment
    }
    ...RepositoryInfoFragment
  }
  ${REPOSITORY_INFO_FRAGMENT}
  ${SCHEDULER_FRAGMENT}
`;

export const SCHEDULE_FRAGMENT = gql`
  fragment ScheduleFragment on Schedule {
    id
    name
    cronSchedule
    executionTimezone
    pipelineName
    solidSelection
    mode
    partitionSet {
      name
    }
    scheduleState {
      id
      ...ScheduleStateFragment
    }
    futureTicks(limit: 1) {
      results {
        timestamp
      }
    }
  }
  ${SCHEDULE_STATE_FRAGMENT}
`;

export const SCHEDULES_ROOT_QUERY = gql`
  query SchedulesRootQuery($repositorySelector: RepositorySelector!, $jobType: JobType!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      __typename
      ... on Repository {
        id
        ...RepositorySchedulesFragment
      }
      ...PythonErrorFragment
    }
    scheduler {
      ...SchedulerFragment
    }
    unloadableJobStatesOrError(jobType: $jobType) {
      ... on JobStates {
        results {
          id
          ...JobStateFragment
        }
      }
      ...PythonErrorFragment
    }
  }

  ${SCHEDULE_FRAGMENT}
  ${SCHEDULER_FRAGMENT}
  ${PythonErrorInfo.fragments.PythonErrorFragment}
  ${REPOSITORY_SCHEDULES_FRAGMENT}
  ${JOB_STATE_FRAGMENT}
`;

export const SchedulerTimezoneNote: React.FC<{
  schedulerOrError: SchedulerFragment;
}> = ({schedulerOrError}) => {
  if (
    schedulerOrError.__typename !== 'Scheduler' ||
    schedulerOrError.schedulerClass !== 'SystemCronScheduler'
  ) {
    return null;
  }

  return (
    <div
      style={{
        color: Colors.GRAY3,
        fontSize: 12.5,
      }}
    >
      Schedule cron intervals displayed below are in the system time of the machine running the
      scheduler.
    </div>
  );
};
