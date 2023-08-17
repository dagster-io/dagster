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
          jobOriginId: string;
          name: string;
          targets: Array<{__typename: 'Target'; pipelineName: string; mode: string}> | null;
          sensorState: {
            __typename: 'InstigationState';
            id: string;
            selectorId: string;
            status: Types.InstigationStatus;
          };
        }>;
      }
    | {__typename: 'PipelineNotFoundError'}
    | {__typename: 'PythonError'};
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    autoMaterializePolicy: {
      __typename: 'AutoMaterializePolicy';
      policyType: Types.AutoMaterializePolicyType;
    } | null;
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
  autoMaterializePolicy: {
    __typename: 'AutoMaterializePolicy';
    policyType: Types.AutoMaterializePolicyType;
  } | null;
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
    jobOriginId: string;
    name: string;
    targets: Array<{__typename: 'Target'; pipelineName: string; mode: string}> | null;
    sensorState: {
      __typename: 'InstigationState';
      id: string;
      selectorId: string;
      status: Types.InstigationStatus;
    };
  }>;
};

export type RunMetadataFragment = {
  __typename: 'Run';
  id: string;
  status: Types.RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
  assets: Array<{
    __typename: 'Asset';
    id: string;
    key: {__typename: 'AssetKey'; path: Array<string>};
  }>;
};
