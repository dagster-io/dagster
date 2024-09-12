// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ScheduleAssetSelectionQueryVariables = Types.Exact<{
  scheduleSelector: Types.ScheduleSelector;
}>;

export type ScheduleAssetSelectionQuery = {
  __typename: 'Query';
  scheduleOrError:
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
        __typename: 'Schedule';
        id: string;
        assetSelection: {
          __typename: 'AssetSelection';
          assetSelectionString: string | null;
          assetsOrError:
            | {
                __typename: 'AssetConnection';
                nodes: Array<{
                  __typename: 'Asset';
                  id: string;
                  key: {__typename: 'AssetKey'; path: Array<string>};
                  definition: {
                    __typename: 'AssetNode';
                    id: string;
                    autoMaterializePolicy: {__typename: 'AutoMaterializePolicy'} | null;
                  } | null;
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
        } | null;
      }
    | {__typename: 'ScheduleNotFoundError'};
};

export const ScheduleAssetSelectionQueryVersion = 'ff337e4645f6881b8240ef02dc13ef8dcdee46de71badedd37eb811bab741b87';
