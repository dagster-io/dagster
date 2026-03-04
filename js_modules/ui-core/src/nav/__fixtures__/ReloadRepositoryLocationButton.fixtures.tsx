import {MockedResponse} from '@apollo/client/testing';

import {PERMISSIONS_QUERY} from '../../app/Permissions';
import {PermissionsQuery} from '../../app/types/Permissions.types';
import {buildPermission} from '../../graphql/types';

export const buildPermissionsQuery = (canReload: boolean): MockedResponse<PermissionsQuery> => {
  return {
    request: {
      query: PERMISSIONS_QUERY,
    },
    result: {
      data: {
        __typename: 'Query',
        unscopedPermissions: [],
        locationStatusesOrError: {
          __typename: 'WorkspaceLocationStatusEntries',
          entries: [
            {
              __typename: 'WorkspaceLocationStatusEntry',
              id: 'foobar',
              name: 'foobar',
              permissions: [
                buildPermission({
                  permission: 'reload_repository_location',
                  value: canReload,
                  disabledReason: canReload ? null : 'nope',
                }),
              ],
            },
          ],
        },
      },
    },
  };
};
