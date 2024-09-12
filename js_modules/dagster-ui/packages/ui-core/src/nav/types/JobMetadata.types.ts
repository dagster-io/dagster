// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type JobMetadataQueryVariables = Types.Exact<{
  params: Types.PipelineSelector;
  runsFilter: Types.RunsFilter;
}>;

export type JobMetadataQuery = {
  __typename: 'Query';
  pipelineOrError:
    | {__typename: 'InvalidSubsetError'}
    | {
        __typename: 'Pipeline';
        id: string;
        isJob: boolean;
        name: string;
        schedules: Array<{
          __typename: 'Schedule';
          id: string;
          mode: string;
          name: string;
          cronSchedule: string;
          executionTimezone: string | null;
          scheduleState: {
            __typename: 'InstigationState';
            id: string;
            selectorId: string;
            status: Types.InstigationStatus;
          };
        }>;
        sensors: Array<{
          __typename: 'Sensor';
          id: string;
          name: string;
          sensorType: Types.SensorType;
          targets: Array<{__typename: 'Target'; pipelineName: string; mode: string}> | null;
          sensorState: {
            __typename: 'InstigationState';
            id: string;
            selectorId: string;
            status: Types.InstigationStatus;
            typeSpecificData:
              | {__typename: 'ScheduleData'}
              | {__typename: 'SensorData'; lastCursor: string | null}
              | null;
          };
        }>;
      }
    | {__typename: 'PipelineNotFoundError'}
    | {__typename: 'PythonError'};
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    autoMaterializePolicy: {__typename: 'AutoMaterializePolicy'} | null;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
  }>;
  pipelineRunsOrError:
    | {__typename: 'InvalidPipelineRunsFilterError'}
    | {__typename: 'PythonError'}
    | {
        __typename: 'Runs';
        results: Array<{
          __typename: 'Run';
          id: string;
          status: Types.RunStatus;
          creationTime: number;
          startTime: number | null;
          endTime: number | null;
          updateTime: number | null;
          assets: Array<{
            __typename: 'Asset';
            id: string;
            key: {__typename: 'AssetKey'; path: Array<string>};
          }>;
        }>;
      };
};

export type JobMetadataAssetNodeFragment = {
  __typename: 'AssetNode';
  id: string;
  autoMaterializePolicy: {__typename: 'AutoMaterializePolicy'} | null;
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
};

export type JobMetadataFragment = {
  __typename: 'Pipeline';
  id: string;
  isJob: boolean;
  name: string;
  schedules: Array<{
    __typename: 'Schedule';
    id: string;
    mode: string;
    name: string;
    cronSchedule: string;
    executionTimezone: string | null;
    scheduleState: {
      __typename: 'InstigationState';
      id: string;
      selectorId: string;
      status: Types.InstigationStatus;
    };
  }>;
  sensors: Array<{
    __typename: 'Sensor';
    id: string;
    name: string;
    sensorType: Types.SensorType;
    targets: Array<{__typename: 'Target'; pipelineName: string; mode: string}> | null;
    sensorState: {
      __typename: 'InstigationState';
      id: string;
      selectorId: string;
      status: Types.InstigationStatus;
      typeSpecificData:
        | {__typename: 'ScheduleData'}
        | {__typename: 'SensorData'; lastCursor: string | null}
        | null;
    };
  }>;
};

export type RunMetadataFragment = {
  __typename: 'Run';
  id: string;
  status: Types.RunStatus;
  creationTime: number;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
  assets: Array<{
    __typename: 'Asset';
    id: string;
    key: {__typename: 'AssetKey'; path: Array<string>};
  }>;
};

export const JobMetadataQueryVersion = 'e44915164a1174b291978e4bee269eb293e3953dc6d5fa5831a731b2533e1bf5';
