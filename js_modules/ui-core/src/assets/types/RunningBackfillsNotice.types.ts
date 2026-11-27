/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunningBackfillsNoticeQueryVariables = Exact<{[key: string]: never}>;

export type RunningBackfillsNoticeQuery = {
  __typename: 'Query';
  partitionBackfillsOrError:
    | {
        __typename: 'PartitionBackfills';
        results: Array<{
          __typename: 'PartitionBackfill';
          id: string;
          partitionSetName: string | null;
          assetSelection: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
        }>;
      }
    | {__typename: 'PythonError'};
};

export const RunningBackfillsNoticeQueryVersion = 'edaaca1d6474672ae342eb3887f2aed16fbb502b704a603986d21f14bc10ee53';
