import {gql, useApolloClient, useMutation, useQuery} from '@apollo/client';
import {Intent} from '@blueprintjs/core';
import * as React from 'react';

import {SharedToaster} from '../app/DomUtils';
import {useInvalidateConfigsForRepo} from '../app/LocalStorage';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment';
import {RepositoryLocationLoadStatus} from '../types/globalTypes';

import {
  ReloadRepositoryLocationMutation,
  ReloadRepositoryLocationMutationVariables,
} from './types/ReloadRepositoryLocationMutation';
import {RepositoryLocationStatusQuery} from './types/RepositoryLocationStatusQuery';

type State = {
  mutating: boolean;
  pollStartTime: number | null;
  error: PythonErrorFragment | {message: string} | null;
};

type Action =
  | {type: 'start-mutation'}
  | {type: 'finish-mutation-and-start-polling'}
  | {type: 'finish-polling'}
  | {type: 'error'; error: PythonErrorFragment | {message: string} | null}
  | {type: 'success'};

const reducer = (state: State, action: Action) => {
  switch (action.type) {
    case 'start-mutation':
      return {...state, mutating: true, pollStartTime: null};
    case 'finish-mutation-and-start-polling':
      return {...state, mutating: false, pollStartTime: Date.now()};
    case 'finish-polling':
      return {...state, pollStartTime: null};
    case 'error':
      return {...state, mutating: false, error: action.error, pollStartTime: null};
    case 'success':
      return {...state, error: null, pollStartTime: null};
    default:
      return state;
  }
};

const initialState: State = {
  mutating: false,
  pollStartTime: null,
  error: null,
};

const THREE_MINUTES = 3 * 60 * 1000;

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

  const {startPolling, stopPolling} = useQuery<RepositoryLocationStatusQuery>(
    REPOSITORY_LOCATION_STATUS_QUERY,
    {
      skip: state.pollStartTime === null,
      pollInterval: 5000,
      fetchPolicy: 'no-cache',
      // This is irritating, but apparently necessary for now.
      // https://github.com/apollographql/apollo-client/issues/5531
      notifyOnNetworkStatusChange: true,
      onCompleted: (data: RepositoryLocationStatusQuery) => {
        const workspace = data.workspaceOrError;

        // On any failure, immediately show the error dialog. This is a blocking failure that must be
        // either retried after repairing the issue or dismissed manually.
        if (workspace.__typename !== 'Workspace') {
          dispatch({type: 'error', error: {message: 'Failed to load workspace.'}});
          stopPolling();
          return;
        }

        const match = workspace.locationEntries.find((l) => l.id === location);
        if (!match) {
          dispatch({
            type: 'error',
            error: {message: `Location ${location} not found in workspace.`},
          });
          stopPolling();
          return;
        }

        // If we're still loading, there's nothing to do yet. Continue polling unless
        // we have hit our timeout threshold.
        if (match.loadStatus === RepositoryLocationLoadStatus.LOADING) {
          if (Date.now() - Number(state.pollStartTime) > THREE_MINUTES) {
            dispatch({
              type: 'error',
              error: {message: 'Timed out waiting for the location to reload.'},
            });
            stopPolling();
          }
          return;
        }

        // If we're done loading and an error persists, show it.
        if (match.locationOrLoadError?.__typename === 'PythonError') {
          dispatch({type: 'error', error: match.locationOrLoadError});
          stopPolling();
          return;
        }

        // Otherwise, we have no errors left.
        dispatch({type: 'finish-polling'});
        stopPolling();

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
          match?.__typename === 'WorkspaceLocationEntry' &&
          match.locationOrLoadError?.__typename === 'RepositoryLocation'
            ? match.locationOrLoadError.repositories
            : [];

        invalidateConfigs(repositories);

        // Clear and refetch all the queries bound to the UI.
        apollo.resetStore();
      },
    },
  );

  const tryReload = React.useCallback(async () => {
    dispatch({type: 'start-mutation'});
    const {data} = await reload();

    if (data?.reloadRepositoryLocation.__typename === 'WorkspaceLocationEntry') {
      // If the mutation occurs successfully, begin polling.
      dispatch({type: 'finish-mutation-and-start-polling'});
      startPolling(5000);
    } else {
      // Otherwise, surface the error.
      dispatch({
        type: 'error',
        error: {message: data?.reloadRepositoryLocation.message || 'An unexpected error occurred.'},
      });
    }
  }, [reload, startPolling]);

  const {mutating, pollStartTime, error} = state;
  const reloading = mutating || pollStartTime !== null;

  return React.useMemo(() => ({reloading, error, tryReload}), [reloading, error, tryReload]);
};

const RELOAD_REPOSITORY_LOCATION_MUTATION = gql`
  mutation ReloadRepositoryLocationMutation($location: String!) {
    reloadRepositoryLocation(repositoryLocationName: $location) {
      __typename
      ... on WorkspaceLocationEntry {
        id
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
`;

const REPOSITORY_LOCATION_STATUS_QUERY = gql`
  query RepositoryLocationStatusQuery {
    workspaceOrError {
      __typename
      ... on Workspace {
        locationEntries {
          __typename
          id
          loadStatus
          locationOrLoadError {
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
              ...PythonErrorFragment
            }
          }
        }
      }
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
