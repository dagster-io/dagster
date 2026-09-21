/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type PermissionsQueryVariables = Exact<{[key: string]: never}>;

export type PermissionsQuery = {
  __typename: 'Query';
  unscopedPermissions: Array<{
    __typename: 'Permission';
    permission: string;
    value: boolean;
    disabledReason: string | null;
  }>;
  locationStatusesOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'WorkspaceLocationStatusEntries';
        entries: Array<{
          __typename: 'WorkspaceLocationStatusEntry';
          id: string;
          name: string;
          permissions: Array<{
            __typename: 'Permission';
            permission: string;
            value: boolean;
            disabledReason: string | null;
          }>;
        }>;
      };
};

export type PermissionFragment = {
  __typename: 'Permission';
  permission: string;
  value: boolean;
  disabledReason: string | null;
};

export const PermissionsQueryVersion = '505a351d43369bd83e7d4ff2d974368d2a754a85661dfb077a26d1a11ff2f714';
