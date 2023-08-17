// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetWipeMutationVariables = Types.Exact<{
  assetKeys: Array<Types.AssetKeyInput> | Types.AssetKeyInput;
}>;

export type AssetWipeMutation = {
  __typename: 'Mutation';
  wipeAssets:
    | {__typename: 'AssetNotFoundError'}
    | {
        __typename: 'AssetWipeSuccess';
        assetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
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
      }
    | {__typename: 'UnauthorizedError'};
};
