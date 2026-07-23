/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type InstanceConfigQueryVariables = Exact<{[key: string]: never}>;

export type InstanceConfigQuery = {
  __typename: 'Query';
  version: string;
  instance: {__typename: 'Instance'; id: string; info: string | null};
};

export const InstanceConfigQueryVersion = 'bcc75f020d292abb1e2d27cf924ec84a3c1a48f7f24a216e5ec0ed2864becc7a';
