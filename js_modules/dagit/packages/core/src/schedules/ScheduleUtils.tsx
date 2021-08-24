import {gql} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {INSTANCE_HEALTH_FRAGMENT} from '../instance/InstanceHealthFragment';
import {INSTIGATION_STATE_FRAGMENT} from '../instigation/InstigationUtils';
import {REPOSITORY_INFO_FRAGMENT} from '../workspace/RepositoryInformation';

import {SCHEDULER_FRAGMENT} from './SchedulerInfo';
import {SchedulerFragment} from './types/SchedulerFragment';

export const SCHEDULE_FRAGMENT = gql`
  fragment ScheduleFragment on Schedule {
    id
    name
    cronSchedule
    executionTimezone
    pipelineName
    solidSelection
    mode
    description
    partitionSet {
      id
      name
    }
    scheduleState {
      id
      ...InstigationStateFragment
    }
    futureTicks(limit: 5) {
      results {
        timestamp
      }
    }
  }
  ${INSTIGATION_STATE_FRAGMENT}
`;

export const REPOSITORY_SCHEDULES_FRAGMENT = gql`
  fragment RepositorySchedulesFragment on Repository {
    name
    id
    location {
      id
      name
    }
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
  query SchedulesRootQuery(
    $repositorySelector: RepositorySelector!
    $instigationType: InstigationType!
  ) {
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
    unloadableInstigationStatesOrError(instigationType: $instigationType) {
      ... on InstigationStates {
        results {
          id
          ...InstigationStateFragment
        }
      }
      ...PythonErrorFragment
    }
    instance {
      ...InstanceHealthFragment
    }
  }

  ${SCHEDULER_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
  ${REPOSITORY_SCHEDULES_FRAGMENT}
  ${INSTIGATION_STATE_FRAGMENT}
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
