import {gql, useApolloClient, useMutation} from '@apollo/client';
import {Intent} from '@blueprintjs/core';
import * as React from 'react';

import {SharedToaster} from '../app/DomUtils';
import {useInvalidateConfigsForRepo} from '../app/LocalStorage';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment';

import {
  ReloadRepositoryLocationMutation,
  ReloadRepositoryLocationMutationVariables,
} from './types/ReloadRepositoryLocationMutation';

type State = {
  reloading: boolean;
  error: PythonErrorFragment | {message: string} | null;
};

type Action =
  | {type: 'start-reloading'}
  | {type: 'finish-reloading'}
  | {type: 'error'; error: PythonErrorFragment | {message: string} | null}
  | {type: 'success'};

const reducer = (state: State, action: Action) => {
  switch (action.type) {
    case 'start-reloading':
      return {...state, reloading: true};
    case 'finish-reloading':
      return {...state, reloading: false};
    case 'error':
      return {...state, error: action.error};
    case 'success':
      return {...state, error: null};
    default:
      return state;
  }
};

const initialState: State = {
  reloading: false,
  error: null,
};

export const useRepositoryLocationReload = (location: string) => {
  const [state, dispatch] = React.useReducer(reducer, initialState);
  const apollo = useApolloClient();
  const [reload] = useMutation<
    ReloadRepositoryLocationMutation,
    ReloadRepositoryLocationMutationVariables
  >(RELOAD_REPOSITORY_LOCATION_MUTATION, {
    variables: {location},
    fetchPolicy: 'no-cache',
  });

  const invalidateConfigs = useInvalidateConfigsForRepo();

  const tryReload = React.useCallback(async () => {
    dispatch({type: 'start-reloading'});
    const {data} = await reload();
    dispatch({type: 'finish-reloading'});

    let loadFailure = null;
    if (data?.reloadRepositoryLocation.__typename === 'WorkspaceLocationEntry') {
      if (data?.reloadRepositoryLocation.locationOrLoadError?.__typename === 'PythonError') {
        loadFailure = data?.reloadRepositoryLocation.locationOrLoadError;
      }
    } else {
      loadFailure = data?.reloadRepositoryLocation.message
        ? {message: data?.reloadRepositoryLocation.message}
        : null;
    }

    // On failure, immediately show the error dialog. This is a blocking failure that must be
    // either retried after repairing the issue or dismissed manually.
    if (loadFailure) {
      dispatch({type: 'error', error: loadFailure});
      return;
    }

    // On success, show the successful toast, hide the dialog (if open), and reset Apollo.
    SharedToaster.show({
      message: 'Repository location reloaded',
      timeout: 3000,
      icon: 'refresh',
      intent: Intent.SUCCESS,
    });
    dispatch({type: 'success'});

    // Update run config localStorage, which may now be out of date.
    const repositories =
      data?.reloadRepositoryLocation.__typename === 'WorkspaceLocationEntry' &&
      data.reloadRepositoryLocation.locationOrLoadError?.__typename === 'RepositoryLocation'
        ? data.reloadRepositoryLocation.locationOrLoadError.repositories
        : [];

    invalidateConfigs(repositories);

    // Clear and refetch all the queries bound to the UI.
    apollo.resetStore();
  }, [apollo, invalidateConfigs, reload]);

  const {reloading, error} = state;

  return React.useMemo(() => ({reloading, error, tryReload}), [reloading, error, tryReload]);
};

const RELOAD_REPOSITORY_LOCATION_MUTATION = gql`
  mutation ReloadRepositoryLocationMutation($location: String!) {
    reloadRepositoryLocation(repositoryLocationName: $location) {
      __typename
      ... on WorkspaceLocationEntry {
        id
        name
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
          ...PythonErrorFragment
        }
      }
      ... on UnauthorizedError {
        message
      }
      ... on ReloadNotSupported {
        message
      }
      ... on RepositoryLocationNotFound {
        message
      }
      ... on PythonError {
        message
      }
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
