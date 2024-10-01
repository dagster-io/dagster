// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type StartSensorMutationVariables = Types.Exact<{
  sensorSelector: Types.SensorSelector;
}>;

export type StartSensorMutation = {
  __typename: 'Mutation';
  startSensor:
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
          selectorId: string;
          name: string;
          instigationType: Types.InstigationType;
          status: Types.InstigationStatus;
          runningCount: number;
        };
      }
    | {__typename: 'SensorNotFoundError'; message: string}
    | {__typename: 'UnauthorizedError'; message: string};
};

export type StopRunningSensorMutationVariables = Types.Exact<{
  id: Types.Scalars['String']['input'];
}>;

export type StopRunningSensorMutation = {
  __typename: 'Mutation';
  stopSensor:
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
        __typename: 'StopSensorMutationResult';
        instigationState: {
          __typename: 'InstigationState';
          id: string;
          selectorId: string;
          name: string;
          instigationType: Types.InstigationType;
          status: Types.InstigationStatus;
          runningCount: number;
        } | null;
      }
    | {__typename: 'UnauthorizedError'; message: string};
};

export type ResetSensorMutationVariables = Types.Exact<{
  sensorSelector: Types.SensorSelector;
}>;

export type ResetSensorMutation = {
  __typename: 'Mutation';
  resetSensor:
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
        sensorState: {__typename: 'InstigationState'; id: string; status: Types.InstigationStatus};
      }
    | {__typename: 'SensorNotFoundError'; message: string}
    | {__typename: 'UnauthorizedError'; message: string};
};

export const StartSensorVersion = 'd091651f745822f99d00968a3d5bd8bc68c11061bdcb2391d06f5ef6f5775ed9';

export const StopRunningSensorVersion = '810e2b80630b6c8f5a037fbf31eb2d8ece51d4168973270e6d2249e45d064b81';

export const ResetSensorVersion = 'fba64da1f1979a7c53b618ba02c58cb72bd20c06220eeeef0318b15b502e3783';
