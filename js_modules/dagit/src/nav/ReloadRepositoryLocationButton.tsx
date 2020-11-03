import {gql, useApolloClient, useMutation} from '@apollo/client';
import {Button, Icon, Intent, Spinner, Tooltip} from '@blueprintjs/core';
import * as React from 'react';

import {SharedToaster} from 'src/DomUtils';
import {ShortcutHandler} from 'src/ShortcutHandler';
import {
  ReloadRepositoryLocationMutation,
  ReloadRepositoryLocationMutationVariables,
} from 'src/nav/types/ReloadRepositoryLocationMutation';

export type ReloadResult = {type: 'success'} | {type: 'error'; message: string};

interface Props {
  location: string;
  onReload: (location: string, result: ReloadResult) => void;
}

export const ReloadRepositoryLocationButton: React.FC<Props> = (props) => {
  const {location, onReload} = props;
  const apollo = useApolloClient();
  const [reload] = useMutation<
    ReloadRepositoryLocationMutation,
    ReloadRepositoryLocationMutationVariables
  >(RELOAD_REPOSITORY_LOCATION_MUTATION, {
    variables: {location},
  });
  const [reloading, setReloading] = React.useState(false);

  const onClick = async (e: React.MouseEvent | KeyboardEvent) => {
    e.stopPropagation();

    setReloading(true);
    const {data} = await reload();
    setReloading(false);

    let loadFailure = null;
    switch (data?.reloadRepositoryLocation.__typename) {
      case 'RepositoryLocation':
        break;
      case 'RepositoryLocationLoadFailure':
        loadFailure = data?.reloadRepositoryLocation.error.message;
        break;
      default:
        loadFailure = data?.reloadRepositoryLocation.message;
        break;
    }

    if (loadFailure) {
      onReload(location, {type: 'error', message: loadFailure});
    } else {
      SharedToaster.show({
        message: 'Repository Location Reloaded',
        timeout: 3000,
        icon: 'refresh',
        intent: Intent.SUCCESS,
      });
      onReload(location, {type: 'success'});

      // clears and re-fetches all the queries bound to the UI
      apollo.resetStore();
    }
  };

  return (
    <ShortcutHandler
      onShortcut={onClick}
      shortcutLabel={`⌥R`}
      shortcutFilter={(e) => e.keyCode === 82 && e.altKey}
    >
      <Tooltip
        className="bp3-dark"
        hoverOpenDelay={500}
        hoverCloseDelay={0}
        content={'Reload metadata from this repository location.'}
      >
        <Button
          icon={reloading ? <Spinner size={12} /> : <Icon icon="refresh" iconSize={12} />}
          disabled={reloading}
          onClick={onClick}
        />
      </Tooltip>
    </ShortcutHandler>
  );
};

const RELOAD_REPOSITORY_LOCATION_MUTATION = gql`
  mutation ReloadRepositoryLocationMutation($location: String!) {
    reloadRepositoryLocation(repositoryLocationName: $location) {
      __typename
      ... on ReloadNotSupported {
        message
      }
      ... on RepositoryLocationNotFound {
        message
      }
      ... on RepositoryLocationLoadFailure {
        error {
          message
        }
      }
    }
  }
`;
