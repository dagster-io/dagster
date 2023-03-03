import {MockedResponse} from '@apollo/client/testing';

import {PERMISSIONS_QUERY} from '../../app/Permissions';
import {PermissionsQuery} from '../../app/types/Permissions.types';

export const buildPermissionsQuery = (canReload: boolean): MockedResponse<PermissionsQuery> => {
  return {
    request: {
      query: PERMISSIONS_QUERY,
    },
    result: {
      data: {
        __typename: 'DagitQuery',
        unscopedPermissions: [],
        workspaceOrError: {
          __typename: 'Workspace',
          locationEntries: [
            {
              __typename: 'WorkspaceLocationEntry',
              id: 'foobar',
              name: 'foobar',
              permissions: [
                {
                  __typename: 'Permission',
                  permission: 'reload_repository_location',
                  value: canReload,
                  disabledReason: canReload ? null : 'nope',
                },
              ],
            },
          ],
        },
      },
    },
  };
};
