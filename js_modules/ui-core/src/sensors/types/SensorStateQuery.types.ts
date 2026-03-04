// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

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

export const SensorStateQueryVersion = '867ed8f85db89c801fcd6f099356971c9c8a64ce52e6c61e6b73dc18680439aa';
