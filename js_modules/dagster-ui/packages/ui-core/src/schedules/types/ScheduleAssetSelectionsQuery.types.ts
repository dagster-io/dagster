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
          assetChecks: Array<{
            __typename: 'AssetCheckhandle';
            name: string;
            assetKey: {__typename: 'AssetKey'; path: Array<string>};
          }>;
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
                    automationCondition: {__typename: 'AutomationCondition'} | null;
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

export const ScheduleAssetSelectionQueryVersion = '33af4b2d37d581ed3da0226f0877ad73a1ad46ab9c8938a19509fc4f851c78bb';
