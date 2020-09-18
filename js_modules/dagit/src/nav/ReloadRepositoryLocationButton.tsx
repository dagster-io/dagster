import {Button, Icon, Intent, Spinner, Tooltip} from '@blueprintjs/core';
import gql from 'graphql-tag';
import * as React from 'react';
import {useApolloClient, useMutation} from 'react-apollo';

import {SharedToaster} from '../DomUtils';
import {ShortcutHandler} from '../ShortcutHandler';

import {
  ReloadRepositoryLocationMutation,
  ReloadRepositoryLocationMutationVariables,
} from './types/ReloadRepositoryLocationMutation';

export const ReloadRepositoryLocationButton: React.FunctionComponent<{
  location: string;
}> = ({location}) => {
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

    const error =
      data?.reloadRepositoryLocation.__typename !== 'RepositoryLocation'
        ? data?.reloadRepositoryLocation.message
        : null;

    if (error) {
      SharedToaster.show({
        message: error,
        timeout: 3000,
        icon: 'error',
        intent: Intent.DANGER,
      });
    } else {
      SharedToaster.show({
        message: 'Repository Location Reloaded',
        timeout: 3000,
        icon: 'refresh',
        intent: Intent.SUCCESS,
      });

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
    }
  }
`;
