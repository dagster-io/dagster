// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SensorSwitchFragment = {
  __typename: 'Sensor';
  id: string;
  name: string;
  sensorType: Types.SensorType;
  sensorState: {
    __typename: 'InstigationState';
    id: string;
    selectorId: string;
    status: Types.InstigationStatus;
    typeSpecificData:
      | {__typename: 'ScheduleData'}
      | {__typename: 'SensorData'; lastCursor: string | null}
      | null;
  };
};

export type SensorStateQueryVariables = Types.Exact<{
  sensorSelector: Types.SensorSelector;
}>;

export type SensorStateQuery = {
  __typename: 'Query';
  sensorOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Sensor';
        id: string;
        sensorState: {__typename: 'InstigationState'; id: string; status: Types.InstigationStatus};
      }
    | {__typename: 'SensorNotFoundError'}
    | {__typename: 'UnauthorizedError'};
};
