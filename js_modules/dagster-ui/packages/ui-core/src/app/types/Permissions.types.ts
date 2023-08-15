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
  workspaceOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Workspace';
        id: string;
        locationEntries: Array<{
          __typename: 'WorkspaceLocationEntry';
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
