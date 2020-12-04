import {gql} from '@apollo/client';

import {REPOSITORY_ORIGIN_FRAGMENT} from 'src/RepositoryInformation';

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
    }
    runsCount
    ticks(limit: 1) {
      id
      status
      timestamp
    }
  }
  ${REPOSITORY_ORIGIN_FRAGMENT}
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
