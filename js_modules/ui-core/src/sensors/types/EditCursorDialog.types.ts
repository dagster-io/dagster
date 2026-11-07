/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type InstigationStatus = 'RUNNING' | 'STOPPED';

export type SensorSelector = {
  repositoryLocationName: string;
  repositoryName: string;
  sensorName: string;
};

export type SetSensorCursorMutationVariables = Exact<{
  sensorSelector: Types.SensorSelector;
  cursor?: string | null | undefined;
}>;

export type SetSensorCursorMutation = {
  __typename: 'Mutation';
  setSensorCursor:
    | {
        __typename: 'PythonError';
        message: string;
        stack: Array<string>;
        errorChain: Array<{
          __typename: 'ErrorChainLink';
          isExplicitLink: boolean;
          error: {__typename: 'PythonError'; message: string; stack: Array<string>};
        }>;
      }
    | {
        __typename: 'Sensor';
        id: string;
        sensorState: {
          __typename: 'InstigationState';
          id: string;
          status: Types.InstigationStatus;
          typeSpecificData:
            | {__typename: 'ScheduleData'}
            | {__typename: 'SensorData'; lastCursor: string | null}
            | null;
        };
      }
    | {__typename: 'SensorNotFoundError'; message: string}
    | {__typename: 'UnauthorizedError'; message: string};
};

export const SetSensorCursorMutationVersion = '1a13ac198329ec89b5e3e730b334e3e647496b5331451c45e53f073ab2ca9b01';
