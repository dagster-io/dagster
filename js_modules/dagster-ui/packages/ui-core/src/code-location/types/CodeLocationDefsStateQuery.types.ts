// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type CodeLocationDefsStateQueryVariables = Types.Exact<{
  locationName: Types.Scalars['String']['input'];
}>;

export type CodeLocationDefsStateQuery = {
  __typename: 'Query';
  latestDefsStateInfo: {
    __typename: 'DefsStateInfo';
    keyStateInfo: Array<{
      __typename: 'DefsStateInfoEntry';
      name: string;
      info: {
        __typename: 'DefsKeyStateInfo';
        version: string;
        createTimestamp: number;
        managementType: Types.DefsStateManagementType;
      } | null;
    }>;
  } | null;
  workspaceLocationEntryOrError:
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
        __typename: 'WorkspaceLocationEntry';
        id: string;
        defsStateInfo: {
          __typename: 'DefsStateInfo';
          keyStateInfo: Array<{
            __typename: 'DefsStateInfoEntry';
            name: string;
            info: {
              __typename: 'DefsKeyStateInfo';
              version: string;
              createTimestamp: number;
              managementType: Types.DefsStateManagementType;
            } | null;
          }>;
        } | null;
      }
    | null;
};

export const CodeLocationDefsStateQueryVersion = '574502c4307b72bca431bba7be22191dcfcc6a3656566d8677d1abf2efe2b804';
