// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type PermissionsQueryVariables = Types.Exact<{[key: string]: never}>;

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
