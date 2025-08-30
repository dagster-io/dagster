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

export const CodeLocationDefsStateQueryVersion = '48c254f1f69e44eb1010e324b368262b96f00fdc20da873424e12ad76924c2c4';
