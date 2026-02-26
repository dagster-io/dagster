// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type InstanceConfigQueryVariables = Types.Exact<{[key: string]: never}>;

export type InstanceConfigQuery = {
  __typename: 'Query';
  version: string;
  instance: {__typename: 'Instance'; id: string; info: string | null};
};

export const InstanceConfigQueryVersion = 'bcc75f020d292abb1e2d27cf924ec84a3c1a48f7f24a216e5ec0ed2864becc7a';
