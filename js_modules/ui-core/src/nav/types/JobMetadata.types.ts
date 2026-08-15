/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetCheckHandleInput = {
  assetKey: AssetKeyInput;
  name: string;
};

export type AssetKeyInput = {
  path: Array<string>;
};

export type ExecutionTag = {
  key: string;
  value: string;
};

export type InstigationStatus = 'RUNNING' | 'STOPPED';

export type PipelineSelector = {
  assetCheckSelection?: Array<AssetCheckHandleInput> | null | undefined;
  assetSelection?: Array<AssetKeyInput> | null | undefined;
  pipelineName: string;
  repositoryLocationName: string;
  repositoryName: string;
  solidSelection?: Array<string> | null | undefined;
};

export type RunStatus =
  | 'CANCELED'
  | 'CANCELING'
  | 'FAILURE'
  | 'MANAGED'
  | 'NOT_STARTED'
  | 'QUEUED'
  | 'STARTED'
  | 'STARTING'
  | 'SUCCESS';

export type RunsFilter = {
  createdAfter?: number | null | undefined;
  createdBefore?: number | null | undefined;
  mode?: string | null | undefined;
  pipelineName?: string | null | undefined;
  runIds?: Array<string | null | undefined> | null | undefined;
  snapshotId?: string | null | undefined;
  statuses?: Array<RunStatus> | null | undefined;
  tags?: Array<ExecutionTag> | null | undefined;
  updatedAfter?: number | null | undefined;
  updatedBefore?: number | null | undefined;
};

export type SensorType =
  | 'ASSET'
  | 'AUTOMATION'
  | 'AUTO_MATERIALIZE'
  | 'FRESHNESS_POLICY'
  | 'MULTI_ASSET'
  | 'RUN_STATUS'
  | 'STANDARD'
  | 'UNKNOWN';

export type JobMetadataQueryVariables = Exact<{
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
            hasStartPermission: boolean;
            hasStopPermission: boolean;
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
            hasStartPermission: boolean;
            hasStopPermission: boolean;
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
    automationCondition: {__typename: 'AutomationCondition'} | null;
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
  automationCondition: {__typename: 'AutomationCondition'} | null;
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
      hasStartPermission: boolean;
      hasStopPermission: boolean;
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
      hasStartPermission: boolean;
      hasStopPermission: boolean;
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

export const JobMetadataQueryVersion = '42558b05c2bcdea56a428ab77c2f477601fec1628e24b82841e0eb4199e28067';
