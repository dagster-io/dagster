// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type InstanceConfigQueryVariables = Types.Exact<{[key: string]: never}>;

export type InstanceConfigQuery = {
  __typename: 'Query';
  version: string;
  instance: {__typename: 'Instance'; id: string; info: string | null};
};
