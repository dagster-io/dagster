/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type InstigationStatus = 'RUNNING' | 'STOPPED';

export type SensorType =
  | 'ASSET'
  | 'AUTOMATION'
  | 'AUTO_MATERIALIZE'
  | 'FRESHNESS_POLICY'
  | 'MULTI_ASSET'
  | 'RUN_STATUS'
  | 'STANDARD'
  | 'UNKNOWN';

export type AssetInstigatorsQueryVariables = Exact<{[key: string]: never}>;

export type AssetInstigatorsQuery = {
  __typename: 'Query';
  repositoriesOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'RepositoryConnection';
        nodes: Array<{
          __typename: 'Repository';
          id: string;
          sensors: Array<{
            __typename: 'Sensor';
            id: string;
            name: string;
            sensorType: Types.SensorType;
            assetSelection: {
              __typename: 'AssetSelection';
              assetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
            } | null;
            targets: Array<{__typename: 'Target'; pipelineName: string}> | null;
          }>;
          schedules: Array<{
            __typename: 'Schedule';
            id: string;
            name: string;
            pipelineName: string;
            assetSelection: {
              __typename: 'AssetSelection';
              assetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
            } | null;
            scheduleState: {
              __typename: 'InstigationState';
              id: string;
              status: Types.InstigationStatus;
            };
          }>;
        }>;
      }
    | {__typename: 'RepositoryNotFoundError'};
};

export const AssetInstigatorsQueryVersion = 'f6dc693b12e6c5160324bf0d39434f52cee09a76883b023e38546b00ebc638e1';
