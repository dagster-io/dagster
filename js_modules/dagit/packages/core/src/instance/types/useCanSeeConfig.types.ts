// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type InstanceConfigHasInfoQueryVariables = Types.Exact<{[key: string]: never}>;

export type InstanceConfigHasInfoQuery = {
  __typename: 'Query';
  instance: {__typename: 'Instance'; id: string; hasInfo: boolean};
};
