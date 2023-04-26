// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type InstanceConcurrencyLimitsQueryVariables = Types.Exact<{[key: string]: never}>;

export type InstanceConcurrencyLimitsQuery = {
  __typename: 'DagitQuery';
  instance: {
    __typename: 'Instance';
    id: string;
    concurrencyLimits: Array<{
      __typename: 'ConcurrencyLimit';
      id: string;
      concurrencyKey: string;
      limit: number;
      activeRunIds: Array<string>;
      numActive: number;
    }>;
  };
};

export type SetConcurrencyLimitMutationVariables = Types.Exact<{
  concurrencyKey: Types.Scalars['String'];
  limit: Types.Scalars['Int'];
}>;

export type SetConcurrencyLimitMutation = {
  __typename: 'DagitMutation';
  setConcurrencyLimit: boolean;
};
