// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type DefsStateInfoFragment = {
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
};

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

export const CodeLocationDefsStateQueryVersion = '5b08179edb0fd7fc5708a72749481eef52efc1b06874a64ea8d7f87ed1a8afbe';
