import gql from "graphql-tag";
import { SCHEDULER_FRAGMENT } from "./SchedulerInfo";
import PythonErrorInfo from "../PythonErrorInfo";
import { RepositoryInformationFragment } from "../RepositoryInformation";

export const SCHEDULE_STATE_FRAGMENT = gql`
  fragment ScheduleStateFragment on ScheduleState {
    __typename
    id
    scheduleOriginId
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
