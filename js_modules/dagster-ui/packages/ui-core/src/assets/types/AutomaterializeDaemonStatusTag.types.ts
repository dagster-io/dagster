// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type GetAutoMaterializePausedQueryVariables = Types.Exact<{[key: string]: never}>;

export type GetAutoMaterializePausedQuery = {
  __typename: 'Query';
  instance: {__typename: 'Instance'; id: string; autoMaterializePaused: boolean};
};

export type SetAutoMaterializePausedMutationVariables = Types.Exact<{
  paused: Types.Scalars['Boolean'];
}>;

export type SetAutoMaterializePausedMutation = {
  __typename: 'Mutation';
  setAutoMaterializePaused: boolean;
};
