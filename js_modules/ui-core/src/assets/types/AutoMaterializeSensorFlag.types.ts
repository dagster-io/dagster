/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AutoMaterializeSensorFlagQueryVariables = Exact<{[key: string]: never}>;

export type AutoMaterializeSensorFlagQuery = {
  __typename: 'Query';
  instance: {__typename: 'Instance'; id: string; useAutoMaterializeSensors: boolean};
};

export const AutoMaterializeSensorFlagVersion = '961162c030e7e3c35be91db37c1990ad31b53cb8225d216fece2bdc2a6210bce';
