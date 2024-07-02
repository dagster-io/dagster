// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SensorSwitchFragment = {
  __typename: 'InstigationState';
  id: string;
  selectorId: string;
  status: Types.InstigationStatus;
  typeSpecificData:
    | {__typename: 'ScheduleData'}
    | {__typename: 'SensorData'; lastCursor: string | null}
    | null;
};

export type SensorStateQueryVariables = Types.Exact<{
  id: Types.Scalars['String']['input'];
}>;

export type SensorStateQuery = {
  __typename: 'Query';
  instigationStateOrError:
    | {__typename: 'InstigationState'; id: string; status: Types.InstigationStatus}
    | {__typename: 'InstigationStateNotFoundError'}
    | {__typename: 'PythonError'};
};
