// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetsStateQueryVariables = Types.Exact<{
  cursor?: Types.InputMaybe<Types.Scalars['String']['input']>;
  limit?: Types.InputMaybe<Types.Scalars['Int']['input']>;
}>;

export type AssetsStateQuery = {
  __typename: 'Query';
  assetsStateOrError:
    | {
        __typename: 'AssetStateConnection';
        cursor: string | null;
        assets: Array<{
          __typename: 'AssetState';
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

export const AssetsStateQueryVersion = '1ce4680d2785b11790d8bdcceef2740577f265e8b3f5f07929e210f018b57739';
