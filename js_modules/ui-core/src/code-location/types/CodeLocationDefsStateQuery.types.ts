/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type DefsStateManagementType =
  | 'LEGACY_CODE_SERVER_SNAPSHOTS'
  | 'LOCAL_FILESYSTEM'
  | 'VERSIONED_STATE_STORAGE';

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

export type CodeLocationDefsStateQueryVariables = Exact<{
  locationName: string;
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
