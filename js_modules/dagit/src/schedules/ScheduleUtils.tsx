import {gql} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import React from 'react';

import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {RepositoryInformationFragment} from 'src/RepositoryInformation';
import {SCHEDULER_FRAGMENT} from 'src/schedules/SchedulerInfo';
import {SchedulerFragment} from 'src/schedules/types/SchedulerFragment';

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
  ${RepositoryInformationFragment}
`;

export const REPOSITORY_SCHEDULES_FRAGMENT = gql`
  fragment RepositorySchedulesFragment on Repository {
    name
    id
    scheduleDefinitions {
      id
      ...ScheduleDefinitionFragment
    }
    ...RepositoryInfoFragment
  }
  ${RepositoryInformationFragment}
`;

export const SCHEDULE_DEFINITION_FRAGMENT = gql`
  fragment ScheduleDefinitionFragment on ScheduleDefinition {
    id
    name
    cronSchedule
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
  }
  ${SCHEDULE_STATE_FRAGMENT}
`;

export const SCHEDULE_STATES_FRAGMENT = gql`
  fragment ScheduleStatesFragment on ScheduleStates {
    results {
      id
      ...ScheduleStateFragment
    }
  }
  ${SCHEDULE_STATE_FRAGMENT}
`;

export const SCHEDULES_ROOT_QUERY = gql`
  query SchedulesRootQuery($repositorySelector: RepositorySelector!) {
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
    unLoadableScheduleStates: scheduleStatesOrError(
      repositorySelector: $repositorySelector
      withNoScheduleDefinition: true
    ) {
      __typename
      ... on ScheduleStates {
        ...ScheduleStatesFragment
      }
      ...PythonErrorFragment
    }
  }

  ${SCHEDULE_DEFINITION_FRAGMENT}
  ${SCHEDULER_FRAGMENT}
  ${PythonErrorInfo.fragments.PythonErrorFragment}
  ${REPOSITORY_SCHEDULES_FRAGMENT}
  ${SCHEDULE_STATES_FRAGMENT}
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
