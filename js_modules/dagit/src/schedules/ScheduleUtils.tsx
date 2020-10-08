import {Colors} from '@blueprintjs/core';
import gql from 'graphql-tag';
import React from 'react';

import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {RepositoryInformationFragment} from 'src/RepositoryInformation';
import {SCHEDULER_FRAGMENT} from 'src/schedules/SchedulerInfo';

export const SCHEDULE_STATE_FRAGMENT = gql`
  fragment ScheduleStateFragment on ScheduleState {
    __typename
    id
    scheduleOriginId
    repositoryOrigin {
      ... on PythonRepositoryOrigin {
        codePointer {
          metadata {
            key
            value
          }
        }
        executablePath
      }
      ... on GrpcRepositoryOrigin {
        grpcUrl
      }
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
`;

export const SCHEDULE_DEFINITION_FRAGMENT = gql`
  fragment ScheduleDefinitionFragment on ScheduleDefinition {
    name
    cronSchedule
    pipelineName
    solidSelection
    mode
    partitionSet {
      name
    }
    scheduleState {
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
        name
        id
        ...RepositoryInfoFragment
      }
      ...PythonErrorFragment
    }
    scheduler {
      ...SchedulerFragment
    }
    scheduleDefinitionsOrError(repositorySelector: $repositorySelector) {
      ... on ScheduleDefinitions {
        results {
          ...ScheduleDefinitionFragment
        }
      }
      ...PythonErrorFragment
    }
    scheduleStatesOrError(repositorySelector: $repositorySelector, withNoScheduleDefinition: true) {
      __typename
      ... on ScheduleStates {
        results {
          ...ScheduleStateFragment
        }
      }
      ...PythonErrorFragment
    }
  }

  ${SCHEDULE_DEFINITION_FRAGMENT}
  ${SCHEDULER_FRAGMENT}
  ${PythonErrorInfo.fragments.PythonErrorFragment}
  ${RepositoryInformationFragment}
`;

export const SchedulerTimezoneNote = () => (
  <div
    style={{
      color: Colors.GRAY3,
      fontSize: 12.5,
      marginBottom: 20,
    }}
  >
    Schedule cron intervals displayed below are in the system time of the machine running the
    scheduler.
  </div>
);
