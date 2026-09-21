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

export type SensorType =
  | 'ASSET'
  | 'AUTOMATION'
  | 'AUTO_MATERIALIZE'
  | 'FRESHNESS_POLICY'
  | 'MULTI_ASSET'
  | 'RUN_STATUS'
  | 'STANDARD'
  | 'UNKNOWN';

export type SingleJobQueryVariables = Exact<{
  selector: Types.PipelineSelector;
}>;

export type SingleJobQuery = {
  __typename: 'Query';
  pipelineOrError:
    | {__typename: 'InvalidSubsetError'}
    | {
        __typename: 'Pipeline';
        id: string;
        name: string;
        isJob: boolean;
        isAssetJob: boolean;
        description: string | null;
        runs: Array<{
          __typename: 'Run';
          id: string;
          status: Types.RunStatus;
          creationTime: number;
          startTime: number | null;
          endTime: number | null;
          updateTime: number | null;
        }>;
        schedules: Array<{
          __typename: 'Schedule';
          id: string;
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
};

export const SingleJobQueryVersion = '25d7a06c2c616338bb6d6e49f8df1803d82ebd77c94e2229bce8633e1dbd912f';
