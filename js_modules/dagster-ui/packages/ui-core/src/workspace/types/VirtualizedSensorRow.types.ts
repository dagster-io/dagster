// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SingleSensorQueryVariables = Types.Exact<{
  selector: Types.SensorSelector;
}>;

export type SingleSensorQuery = {
  __typename: 'Query';
  sensorOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Sensor';
        id: string;
        description: string | null;
        name: string;
        minIntervalSeconds: number;
        sensorType: Types.SensorType;
        targets: Array<{__typename: 'Target'; pipelineName: string}> | null;
        metadata: {
          __typename: 'SensorMetadata';
          assetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
        };
        sensorState: {
          __typename: 'InstigationState';
          id: string;
          runningCount: number;
          hasStartPermission: boolean;
          hasStopPermission: boolean;
          selectorId: string;
          status: Types.InstigationStatus;
          ticks: Array<{
            __typename: 'InstigationTick';
            id: string;
            status: Types.InstigationTickStatus;
            timestamp: number;
            skipReason: string | null;
            runIds: Array<string>;
            runKeys: Array<string>;
            error: {
              __typename: 'PythonError';
              message: string;
              stack: Array<string>;
              errorChain: Array<{
                __typename: 'ErrorChainLink';
                isExplicitLink: boolean;
                error: {__typename: 'PythonError'; message: string; stack: Array<string>};
              }>;
            } | null;
          }>;
          runs: Array<{
            __typename: 'Run';
            id: string;
            status: Types.RunStatus;
            creationTime: number;
            startTime: number | null;
            endTime: number | null;
            updateTime: number | null;
          }>;
          nextTick: {__typename: 'DryRunInstigationTick'; timestamp: number | null} | null;
          typeSpecificData:
            | {__typename: 'ScheduleData'}
            | {__typename: 'SensorData'; lastCursor: string | null}
            | null;
        };
      }
    | {__typename: 'SensorNotFoundError'}
    | {__typename: 'UnauthorizedError'};
};

export const SingleSensorQueryVersion = '713c94fb89ff1edd1ca419cb2b5eabe4f317dcef7529a3fd6a186ca28e56b62e';
