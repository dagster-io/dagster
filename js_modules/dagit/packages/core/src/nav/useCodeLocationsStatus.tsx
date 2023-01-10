import {useQuery} from '@apollo/client';
import {Box, ButtonLink, Colors} from '@dagster-io/ui';
import * as React from 'react';
import {useHistory} from 'react-router-dom';
import styled from 'styled-components/macro';

import {SharedToaster} from '../app/DomUtils';
import {useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {graphql} from '../graphql';
import {CodeLocationStatusQueryQuery, RepositoryLocationLoadStatus} from '../graphql/graphql';
import {StatusAndMessage} from '../instance/DeploymentStatusType';
import {WorkspaceContext} from '../workspace/WorkspaceContext';

type LocationStatusEntry = {
  loadStatus: RepositoryLocationLoadStatus;
  id: string;
  name: string;
  updateTimestamp: number;
};

const POLL_INTERVAL = 5 * 1000;

type EntriesById = Record<string, LocationStatusEntry>;

export const useCodeLocationsStatus = (skip = false): StatusAndMessage | null => {
  const {locationEntries, refetch} = React.useContext(WorkspaceContext);
  const [previousEntriesById, setPreviousEntriesById] = React.useState<EntriesById | null>(null);

  const history = useHistory();

  const [showSpinner, setShowSpinner] = React.useState(false);

  const onClickViewButton = React.useCallback(() => {
    history.push('/locations');
  }, [history]);

  // Reload the workspace, but don't toast about it.
  const reloadWorkspaceQuietly = React.useCallback(async () => {
    setShowSpinner(true);
    await refetch();
    setShowSpinner(false);
  }, [refetch]);

  // Reload the workspace, and show a success or error toast upon completion.
  const reloadWorkspaceLoudly = React.useCallback(async () => {
    setShowSpinner(true);
    const result = await refetch();
    setShowSpinner(false);

    const anyErrors =
      result.data.workspaceOrError.__typename === 'PythonError' ||
      result.data.workspaceOrError.locationEntries.some(
        (entry) => entry.locationOrLoadError?.__typename === 'PythonError',
      );

    const showViewButton = !alreadyViewingCodeLocations();

    if (anyErrors) {
      SharedToaster.show({
        intent: 'warning',
        message: (
          <Box flex={{direction: 'row', justifyContent: 'space-between', gap: 24, grow: 1}}>
            <div>Definitions loaded with errors</div>
            {showViewButton ? <ViewCodeLocationsButton onClick={onClickViewButton} /> : null}
          </Box>
        ),
        icon: 'check_circle',
      });
    } else {
      SharedToaster.show({
        intent: 'success',
        message: (
          <Box flex={{direction: 'row', justifyContent: 'space-between', gap: 24, grow: 1}}>
            <div>Definitions reloaded</div>
            {showViewButton ? <ViewCodeLocationsButton onClick={onClickViewButton} /> : null}
          </Box>
        ),
        icon: 'check_circle',
      });
    }
  }, [onClickViewButton, refetch]);

  const onLocationUpdate = (data: CodeLocationStatusQueryQuery) => {
    // Given the previous and current code locations, determine whether to show a) a loading spinner
    // and/or b) a toast indicating that a code location is being reloaded.
    const entries =
      data?.locationStatusesOrError?.__typename === 'WorkspaceLocationStatusEntries'
        ? data?.locationStatusesOrError.entries
        : [];

    let hasUpdatedEntries = entries.length !== Object.keys(previousEntriesById || {}).length;
    const currEntriesById: {[key: string]: LocationStatusEntry} = {};
    entries.forEach((entry) => {
      const previousEntry = previousEntriesById && previousEntriesById[entry.id];
      const entryIsUpdated =
        !previousEntry ||
        previousEntry.updateTimestamp < entry.updateTimestamp ||
        previousEntry.loadStatus !== entry.loadStatus;
      hasUpdatedEntries = hasUpdatedEntries || entryIsUpdated;
      currEntriesById[entry.id] = entryIsUpdated
        ? {
            id: entry.id,
            loadStatus: entry.loadStatus,
            name: entry.name,
            updateTimestamp: entry.updateTimestamp,
          }
        : previousEntry;
    });
    const currentEntries = Object.values(currEntriesById || {});
    const previousEntries = Object.values(previousEntriesById || {});
    if (hasUpdatedEntries) {
      setPreviousEntriesById(currEntriesById);
    }

    // At least one code location has been removed. Reload, but don't make a big deal about it
    // since this was probably done manually.
    if (previousEntries.length > currentEntries.length && !hasUpdatedEntries) {
      reloadWorkspaceQuietly();
      return;
    }

    const currentlyLoading = currentEntries.filter(
      ({loadStatus}: LocationStatusEntry) => loadStatus === RepositoryLocationLoadStatus.LOADING,
    );
    const anyCurrentlyLoading = currentlyLoading.length > 0;

    // If this is a fresh pageload and any locations are loading, show the spinner but not the toaster.
    if (!previousEntriesById) {
      if (anyCurrentlyLoading) {
        setShowSpinner(true);
      }
      return;
    }

    const showViewButton = !alreadyViewingCodeLocations();

    // We have a new entry, and it has already finished loading. Wow! It's surprisingly fast for it
    // to have finished loading so quickly, but go ahead and indicate that the location has
    // been added, then reload the workspace.
    if (currentEntries.length > previousEntries.length && !currentlyLoading.length) {
      const previousMap: {[id: string]: true} = previousEntries.reduce(
        (accum, {id}) => ({...accum, [id]: true}),
        {},
      );

      // Count the number of new code locations.
      const addedEntries: string[] = [];
      currentEntries.forEach(({id}) => {
        if (!previousMap.hasOwnProperty(id)) {
          addedEntries.push(id);
        }
      });

      SharedToaster.show({
        intent: 'primary',
        message: (
          <Box flex={{direction: 'row', justifyContent: 'space-between', gap: 24, grow: 1}}>
            {addedEntries.length === 1 ? (
              <span>
                Code location <strong>{addedEntries[0]}</strong> added
              </span>
            ) : (
              <span>{addedEntries.length} code locations added</span>
            )}
            {showViewButton ? <ViewCodeLocationsButton onClick={onClickViewButton} /> : null}
          </Box>
        ),
        icon: 'add_circle',
      });

      reloadWorkspaceLoudly();
      return;
    }

    const anyPreviouslyLoading = previousEntries.some(
      ({loadStatus}) => loadStatus === RepositoryLocationLoadStatus.LOADING,
    );

    // One or more code locations are updating, so let the user know. We will not refetch the workspace
    // until all code locations are done updating.
    if (!anyPreviouslyLoading && anyCurrentlyLoading) {
      setShowSpinner(true);

      SharedToaster.show({
        intent: 'primary',
        message: (
          <Box flex={{direction: 'row', justifyContent: 'space-between', gap: 24, grow: 1}}>
            {currentlyLoading.length === 1 ? (
              <span>
                Updating <strong>{currentlyLoading[0].name}</strong>
              </span>
            ) : (
              <span>Updating {currentlyLoading.length} code locations</span>
            )}
            {showViewButton ? <ViewCodeLocationsButton onClick={onClickViewButton} /> : null}
          </Box>
        ),
        icon: 'refresh',
      });

      return;
    }

    // A location was previously loading, and no longer is. Our workspace is ready. Refetch it.
    if (anyPreviouslyLoading && !anyCurrentlyLoading) {
      reloadWorkspaceLoudly();
      return;
    }

    if (hasUpdatedEntries) {
      reloadWorkspaceLoudly();
      return;
    }
  };

  const queryData = useQuery(CODE_LOCATION_STATUS_QUERY, {
    fetchPolicy: 'network-only',
    notifyOnNetworkStatusChange: true,
    skip,
    onCompleted: onLocationUpdate,
  });

  useQueryRefreshAtInterval(queryData, POLL_INTERVAL);

  if (showSpinner) {
    return {
      type: 'spinner',
      content: <div>Loading definitions…</div>,
    };
  }

  const repoErrors = locationEntries.filter(
    (locationEntry) => locationEntry.locationOrLoadError?.__typename === 'PythonError',
  );

  if (repoErrors.length) {
    return {
      type: 'warning',
      content: (
        <div style={{whiteSpace: 'nowrap'}}>{`${repoErrors.length} ${
          repoErrors.length === 1 ? 'code location failed to load' : 'code locations failed to load'
        }`}</div>
      ),
    };
  }

  return null;
};

const alreadyViewingCodeLocations = () => document.location.pathname.endsWith('/locations');

const ViewCodeLocationsButton: React.FC<{onClick: () => void}> = ({onClick}) => {
  return (
    <ViewButton onClick={onClick} color={Colors.White}>
      View
    </ViewButton>
  );
};

const ViewButton = styled(ButtonLink)`
  white-space: nowrap;
`;

const CODE_LOCATION_STATUS_QUERY = graphql(`
  query CodeLocationStatusQuery {
    locationStatusesOrError {
      __typename
      ... on WorkspaceLocationStatusEntries {
        entries {
          id
          name
          loadStatus
          updateTimestamp
        }
      }
    }
  }
`);
