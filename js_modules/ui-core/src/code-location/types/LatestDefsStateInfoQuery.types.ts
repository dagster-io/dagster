/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type DefsStateManagementType =
  | 'LEGACY_CODE_SERVER_SNAPSHOTS'
  | 'LOCAL_FILESYSTEM'
  | 'VERSIONED_STATE_STORAGE';

export type LatestDefsStateInfoQueryVariables = Exact<{[key: string]: never}>;

export type LatestDefsStateInfoQuery = {
  __typename: 'Query';
  latestDefsStateInfo: {
    __typename: 'DefsStateInfo';
    keyStateInfo: Array<{
      __typename: 'DefsStateInfoEntry';
      name: string;
      info: {
        __typename: 'DefsKeyStateInfo';
        version: string;
        createTimestamp: number;
        managementType: Types.DefsStateManagementType;
      } | null;
    }>;
  } | null;
};

export const LatestDefsStateInfoQueryVersion = '644d3473dec2282a8dfe3c61022bad75d8ed2e356b119c7098c24815301dc9e4';
