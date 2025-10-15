// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type DefsStateInfoFragment = {
  __typename: 'DefsStateInfo';
  keyStateInfo: Array<{
    __typename: 'DefsStateInfoEntry';
    name: string;
    info: {__typename: 'DefsKeyStateInfo'; version: string; createTimestamp: number} | null;
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
      info: {__typename: 'DefsKeyStateInfo'; version: string; createTimestamp: number} | null;
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
            info: {__typename: 'DefsKeyStateInfo'; version: string; createTimestamp: number} | null;
          }>;
        } | null;
      }
    | null;
};

export const CodeLocationDefsStateQueryVersion = '2f58b69f8aacec08df30be6ff3edc6d70afc33a63e7bfd09fe0989f90330c853';
