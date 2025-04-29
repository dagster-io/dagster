// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetsStateQueryVariables = Types.Exact<{
  cursor?: Types.InputMaybe<Types.Scalars['String']['input']>;
  limit?: Types.InputMaybe<Types.Scalars['Int']['input']>;
}>;

export type AssetsStateQuery = {
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

export const AssetsStateQueryVersion = 'e1c06f749930bb076d0761e74bd8312a40ac5622464abfbaa9d591c6bdf5f20d';
