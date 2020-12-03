import {gql} from '@apollo/client';

export const JOB_STATE_FRAGMENT = gql`
  fragment JobStateFragment on JobState {
    id
    name
    jobType
    status
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
    ticks(limit: 1) {
      id
      status
      timestamp
    }
  }
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
