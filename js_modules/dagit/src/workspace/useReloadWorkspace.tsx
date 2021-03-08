import {gql, useApolloClient, useMutation} from '@apollo/client';
import {Intent} from '@blueprintjs/core';
import * as React from 'react';

import {SharedToaster} from 'src/app/DomUtils';
import {useInvalidateConfigsForRepo} from 'src/app/LocalStorage';
import {PYTHON_ERROR_FRAGMENT} from 'src/app/PythonErrorInfo';
import {ReloadWorkspaceMutation} from 'src/workspace/types/ReloadWorkspaceMutation';

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

    if (!data || data?.reloadWorkspace.__typename === 'PythonError') {
      SharedToaster.show({
        message: 'Could not reload workspace.',
        timeout: 3000,
        icon: 'refresh',
        intent: Intent.DANGER,
      });
      return;
    }

    const {nodes} = data.reloadWorkspace;
    SharedToaster.show({
      message: 'Workspace reloaded',
      timeout: 3000,
      icon: 'refresh',
      intent: Intent.SUCCESS,
    });

    const reposToInvalidate = nodes.reduce((accum, location) => {
      if (location.__typename === 'RepositoryLocation') {
        return [...accum, ...location.repositories];
      }
      return accum;
    }, []);

    invalidateConfigs(reposToInvalidate);
    apollo.resetStore();
  };

  return {reloading, onClick};
};

const RELOAD_WORKSPACE_MUTATION = gql`
  mutation ReloadWorkspaceMutation {
    reloadWorkspace {
      ... on RepositoryLocationConnection {
        nodes {
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
          ... on RepositoryLocationLoadFailure {
            id
            error {
              message
            }
          }
        }
      }
      ...PythonErrorFragment
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
