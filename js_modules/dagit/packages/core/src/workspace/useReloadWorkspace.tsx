import {gql, useApolloClient, useMutation} from '@apollo/client';
import * as React from 'react';

import {SharedToaster} from '../app/DomUtils';
import {useInvalidateConfigsForRepo} from '../app/LocalStorage';
import {PYTHON_ERROR_FRAGMENT, UNAUTHORIZED_ERROR_FRAGMENT} from '../app/PythonErrorInfo';

import {
  ReloadWorkspaceMutation,
  ReloadWorkspaceMutation_reloadWorkspace_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories as Repository,
} from './types/ReloadWorkspaceMutation';

export const useReloadWorkspace = () => {
  const apollo = useApolloClient();
  const [reloading, setReloading] = React.useState(false);
  const [reload] = useMutation<ReloadWorkspaceMutation>(RELOAD_WORKSPACE_MUTATION);
  const invalidateConfigs = useInvalidateConfigsForRepo();

  const onClick = async (e: React.MouseEvent | React.KeyboardEvent) => {
    e.stopPropagation();

    setReloading(true);
    const {data} = await reload();
    setReloading(false);

    if (
      !data ||
      data?.reloadWorkspace.__typename === 'PythonError' ||
      data?.reloadWorkspace.__typename === 'UnauthorizedError'
    ) {
      SharedToaster.show({
        message: 'Could not reload workspace.',
        timeout: 3000,
        icon: 'error',
        intent: 'danger',
      });
      return;
    }

    const {locationEntries} = data.reloadWorkspace;
    SharedToaster.show({
      message: 'Workspace reloaded!',
      timeout: 3000,
      icon: 'done',
      intent: 'success',
    });

    const reposToInvalidate = locationEntries.reduce((accum, locationEntry) => {
      if (locationEntry.locationOrLoadError?.__typename === 'RepositoryLocation') {
        return [...accum, ...locationEntry.locationOrLoadError.repositories];
      }
      return accum;
    }, [] as Repository[]);

    invalidateConfigs(reposToInvalidate);
    apollo.resetStore();
  };

  return {reloading, onClick};
};

const RELOAD_WORKSPACE_MUTATION = gql`
  mutation ReloadWorkspaceMutation {
    reloadWorkspace {
      ... on Workspace {
        locationEntries {
          __typename
          name
          id
          loadStatus
          locationOrLoadError {
            __typename
            ... on RepositoryLocation {
              id
              repositories {
                id
                name
                pipelines {
                  id
                  name
                }
              }
            }
            ... on PythonError {
              message
            }
          }
        }
      }
      ...UnauthorizedErrorFragment
      ...PythonErrorFragment
    }
  }
  ${UNAUTHORIZED_ERROR_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
