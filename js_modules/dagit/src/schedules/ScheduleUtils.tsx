import {gql} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import React from 'react';

import {JOB_STATE_FRAGMENT} from 'src/JobUtils';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {REPOSITORY_INFO_FRAGMENT} from 'src/RepositoryInformation';
import {INSTANCE_HEALTH_FRAGMENT} from 'src/instance/InstanceHealthFragment';
import {SCHEDULER_FRAGMENT} from 'src/schedules/SchedulerInfo';
import {SchedulerFragment} from 'src/schedules/types/SchedulerFragment';

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
      partitionStatusesOrError {
        ... on PartitionStatuses {
          results {
            id
            partitionName
            runStatus
          }
        }
      }
    }
    scheduleState {
      id
      ...JobStateFragment
    }
    futureTicks(limit: 5) {
      results {
        timestamp
      }
    }
  }
  ${JOB_STATE_FRAGMENT}
`;

const REPOSITORY_SCHEDULES_FRAGMENT = gql`
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
  ${SCHEDULE_FRAGMENT}
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
    instance {
      ...InstanceHealthFragment
    }
  }

  ${SCHEDULER_FRAGMENT}
  ${PythonErrorInfo.fragments.PythonErrorFragment}
  ${REPOSITORY_SCHEDULES_FRAGMENT}
  ${JOB_STATE_FRAGMENT}
  ${INSTANCE_HEALTH_FRAGMENT}
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
