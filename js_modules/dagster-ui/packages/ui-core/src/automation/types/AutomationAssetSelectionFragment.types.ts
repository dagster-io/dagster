// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AutomationAssetSelectionFragment = {
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
};

export type AssetSelectionNodeFragment = {
  __typename: 'Asset';
  id: string;
  key: {__typename: 'AssetKey'; path: Array<string>};
  definition: {
    __typename: 'AssetNode';
    id: string;
    automationCondition: {__typename: 'AutomationCondition'} | null;
  } | null;
};
