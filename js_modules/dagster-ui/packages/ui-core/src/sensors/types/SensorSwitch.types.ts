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
  id: Types.Scalars['String']['input'];
  selector: Types.InstigationSelector;
}>;

export type SensorStateQuery = {
  __typename: 'Query';
  instigationStateOrError:
    | {
        __typename: 'InstigationState';
        id: string;
        selectorId: string;
        name: string;
        instigationType: Types.InstigationType;
        status: Types.InstigationStatus;
        runningCount: number;
      }
    | {__typename: 'InstigationStateNotFoundError'}
    | {__typename: 'PythonError'};
};
