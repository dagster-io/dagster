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
        jobOriginId: string;
        targets: Array<{__typename: 'Target'; pipelineName: string}> | null;
        metadata: {
          __typename: 'SensorMetadata';
          assetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
        };
        sensorState: {
          __typename: 'InstigationState';
          id: string;
          runningCount: number;
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
            startTime: number | null;
            endTime: number | null;
            updateTime: number | null;
          }>;
          nextTick: {__typename: 'DryRunInstigationTick'; timestamp: number | null} | null;
        };
      }
    | {__typename: 'SensorNotFoundError'}
    | {__typename: 'UnauthorizedError'};
};
