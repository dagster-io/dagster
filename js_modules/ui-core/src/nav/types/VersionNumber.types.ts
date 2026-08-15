/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type VersionNumberQueryVariables = Exact<{[key: string]: never}>;

export type VersionNumberQuery = {__typename: 'Query'; version: string};

export const VersionNumberQueryVersion = '1947790817d11313027a8addb9ceb992f0c79e96f3aa6b99cbece967e3458c40';
