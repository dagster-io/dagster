// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type GetAutoMaterializePausedQueryVariables = Types.Exact<{[key: string]: never}>;

export type GetAutoMaterializePausedQuery = {
  __typename: 'Query';
  instance: {__typename: 'Instance'; id: string; autoMaterializePaused: boolean};
};

export type SetAutoMaterializePausedMutationVariables = Types.Exact<{
  paused: Types.Scalars['Boolean']['input'];
}>;

export type SetAutoMaterializePausedMutation = {
  __typename: 'Mutation';
  setAutoMaterializePaused: boolean;
};

export const GetAutoMaterializePausedQueryVersion = '50f74183f54031274136ab855701d01f26642a6d958d7452ae13aa6c40ca349d';

export const SetAutoMaterializePausedMutationVersion = '144afc0d6f43dfa6d437c0e7f621e4f19ffb48c7f75669d2e3d742c115aa7b4b';
