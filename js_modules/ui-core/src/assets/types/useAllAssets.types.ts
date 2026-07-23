/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetRecordsQueryVariables = Exact<{
  cursor?: string | null | undefined;
  limit?: number | null | undefined;
}>;

export type AssetRecordsQuery = {
  __typename: 'Query';
  assetRecordsOrError:
    | {
        __typename: 'AssetRecordConnection';
        cursor: string | null;
        assets: Array<{
          __typename: 'AssetRecord';
          id: string;
          key: {__typename: 'AssetKey'; path: Array<string>};
        }>;
      }
    | {
        __typename: 'PythonError';
        message: string;
        stack: Array<string>;
        errorChain: Array<{
          __typename: 'ErrorChainLink';
          isExplicitLink: boolean;
          error: {__typename: 'PythonError'; message: string; stack: Array<string>};
        }>;
      };
};

export const AssetRecordsQueryVersion = '1778f6a11acc440983fcf6b6156518b3113c7fa29127130bb30a3e0140807575';
