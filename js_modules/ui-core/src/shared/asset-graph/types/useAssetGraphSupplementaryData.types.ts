// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type AssetInstigatorsQueryVariables = Types.Exact<{[key: string]: never}>;

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
          }>;
          schedules: Array<{
            __typename: 'Schedule';
            id: string;
            name: string;
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

export const AssetInstigatorsQueryVersion = 'ec03eb9a3677674fee93fd8a09267e274fee5d07630647ea50f7076d5f39bc1e';
