// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ReportEventMutationVariables = Types.Exact<{
  eventParams: Types.ReportRunlessAssetEventsParams;
}>;

export type ReportEventMutation = {
  __typename: 'Mutation';
  reportRunlessAssetEvents:
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
    | {
        __typename: 'ReportRunlessAssetEventsSuccess';
        assetKey: {__typename: 'AssetKey'; path: Array<string>};
      }
    | {__typename: 'UnauthorizedError'; message: string};
};
