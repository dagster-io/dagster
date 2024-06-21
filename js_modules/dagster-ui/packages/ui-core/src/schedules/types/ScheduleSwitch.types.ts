// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ScheduleSwitchFragment = {
  __typename: 'InstigationState';
  id: string;
  selectorId: string;
  status: Types.InstigationStatus;
};

export type ScheduleStateQueryVariables = Types.Exact<{
  id: Types.Scalars['String']['input'];
}>;

export type ScheduleStateQuery = {
  __typename: 'Query';
  instigationStateOrError:
    | {__typename: 'InstigationState'; id: string; status: Types.InstigationStatus}
    | {__typename: 'InstigationStateNotFoundError'}
    | {__typename: 'PythonError'};
};
