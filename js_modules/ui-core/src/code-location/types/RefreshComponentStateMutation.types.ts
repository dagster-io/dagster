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

export type RefreshComponentStateMutationVariables = Exact<{
  locationName: string;
  defsStateKey: string;
}>;

export type RefreshComponentStateMutation = {
  __typename: 'Mutation';
  refreshComponentState:
    | {__typename: 'PythonError'; message: string}
    | {__typename: 'RefreshComponentStateAccepted'; locationName: string; defsStateKey: string}
    | {
        __typename: 'RefreshComponentStateError';
        locationName: string;
        defsStateKey: string;
        message: string;
      }
    | {
        __typename: 'RefreshComponentStateSuccess';
        component: {
          __typename: 'Component';
          componentId: string;
          componentType: string;
          isAppManaged: boolean;
          defsStateKey: string | null;
          defsStateInfo: {
            __typename: 'DefsKeyStateInfo';
            version: string;
            createTimestamp: number;
            managementType: Types.DefsStateManagementType;
          } | null;
        };
      }
    | {__typename: 'UnauthorizedError'; message: string};
};

export const RefreshComponentStateMutationVersion = 'efeaf66263eb0d37e7b6da16c1a0397940a0865cb2e420d28b7d9992da8e0ce6';
