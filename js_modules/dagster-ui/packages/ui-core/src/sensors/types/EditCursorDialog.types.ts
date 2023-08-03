// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SetSensorCursorMutationVariables = Types.Exact<{
  sensorSelector: Types.SensorSelector;
  cursor?: Types.InputMaybe<Types.Scalars['String']>;
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
    | {__typename: 'SensorNotFoundError'}
    | {__typename: 'UnauthorizedError'};
};
