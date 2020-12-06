import {gql} from '@apollo/client';

import {TICK_TAG_FRAGMENT} from 'src/JobTick';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {REPOSITORY_INFO_FRAGMENT, REPOSITORY_ORIGIN_FRAGMENT} from 'src/RepositoryInformation';

export const JOB_STATE_FRAGMENT = gql`
  fragment JobStateFragment on JobState {
    id
    name
    jobType
    status
    repositoryOrigin {
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
    status
    runs(limit: 20) {
      id
      runId
      pipelineName
      status
      tags {
        key
        value
      }
    }
    runsCount
    ticks(limit: 1) {
      id
      ...TickTagFragment
    }
    runningCount
  }
  ${REPOSITORY_ORIGIN_FRAGMENT}
  ${PythonErrorInfo.fragments.PythonErrorFragment}
  ${TICK_TAG_FRAGMENT}
`;

export const SENSOR_FRAGMENT = gql`
  fragment SensorFragment on Sensor {
    id
    jobOriginId
    name
    pipelineName
    solidSelection
    mode
    sensorState {
      id
      ...JobStateFragment
    }
  }
  ${JOB_STATE_FRAGMENT}
`;

export const REPOSITORY_SENSORS_FRAGMENT = gql`
  fragment RepositorySensorsFragment on Repository {
    name
    id
    sensors {
      id
      ...SensorFragment
    }
    ...RepositoryInfoFragment
  }
  ${REPOSITORY_INFO_FRAGMENT}
  ${SENSOR_FRAGMENT}
`;
