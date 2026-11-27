/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetEventType = 'ASSET_MATERIALIZATION' | 'ASSET_OBSERVATION';

export type AssetKeyInput = {
  path: Array<string>;
};

export type ReportRunlessAssetEventsParams = {
  assetKey: AssetKeyInput;
  description?: string | null | undefined;
  eventType: AssetEventType;
  partitionKeys?: Array<string | null | undefined> | null | undefined;
};

export type ReportEventMutationVariables = Exact<{
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

export const ReportEventMutationVersion = '80b4987cdf27ec8fac25eb6b98b996bd4fdeb4cbfff605d647da5d4bb8244cb0';
