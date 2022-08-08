import {gql, useQuery} from '@apollo/client';
import {Colors, Icon, Tooltip, Spinner, Box, ButtonLink} from '@dagster-io/ui';
import * as React from 'react';
import {useHistory} from 'react-router-dom';
import styled from 'styled-components/macro';

import {SharedToaster} from '../app/DomUtils';
import {useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {RepositoryLocationLoadStatus} from '../types/globalTypes';
import {WorkspaceContext} from '../workspace/WorkspaceContext';

import {WarningTooltip} from './WarningTooltip';
import {WorkspaceUpdateCheckQuery} from './types/WorkspaceUpdateCheckQuery';

const POLL_INTERVAL = 3 * 1000;

export const WorkspaceStatus = React.memo(() => {
  const {locationEntries, refetch} = React.useContext(WorkspaceContext);
  const history = useHistory();

  const [showSpinner, setShowSpinner] = React.useState(false);

  const queryData = useQuery<WorkspaceUpdateCheckQuery>(WORKSPACE_UPDATE_CHECK_QUERY, {
    fetchPolicy: 'network-only',
    notifyOnNetworkStatusChange: true,
  });

  useQueryRefreshAtInterval(queryData, POLL_INTERVAL);

  const {data, previousData} = queryData;

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

    if (anyErrors) {
      SharedToaster.show({
        intent: 'warning',
        message: (
          <Box flex={{direction: 'row', justifyContent: 'space-between', gap: 24, grow: 1}}>
            <div>Workspace loaded with errors</div>
            <ViewButton onClick={() => history.push('/workspace')} color={Colors.White}>
              View
            </ViewButton>
          </Box>
        ),
        icon: 'check_circle',
      });
    } else {
      SharedToaster.show({
        intent: 'success',
        message: (
          <Box flex={{direction: 'row', justifyContent: 'space-between', gap: 24, grow: 1}}>
            <div>Workspace ready</div>
            <ViewButton onClick={() => history.push('/workspace')} color={Colors.White}>
              View
            </ViewButton>
          </Box>
        ),
        icon: 'check_circle',
      });
    }
  }, [history, refetch]);

  // Given the previous and current code locations, determine whether to show a) a loading spinner
  // and/or b) a toast indicating that a code location is being reloaded.
  React.useEffect(() => {
    const previousEntries =
      previousData?.workspaceOrError.__typename === 'Workspace'
        ? previousData?.workspaceOrError.locationEntries
        : [];
    const currentEntries =
      data?.workspaceOrError.__typename === 'Workspace'
        ? data?.workspaceOrError.locationEntries
        : [];

    // At least one code location has been removed. Reload, but don't make a big deal about it
    // since this was probably done manually.
    if (previousEntries.length > currentEntries.length) {
      reloadWorkspaceQuietly();
      return;
    }

    const currentlyLoading = currentEntries.filter(
      ({loadStatus}) => loadStatus === RepositoryLocationLoadStatus.LOADING,
    );
    const anyCurrentlyLoading = currentlyLoading.length > 0;

    // If this is a fresh pageload and any locations are loading, show the spinner but not the toaster.
    if (!previousData) {
      if (anyCurrentlyLoading) {
        setShowSpinner(true);
      }
      return;
    }

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
            <ViewButton onClick={() => history.push('/workspace')} color={Colors.White}>
              View
            </ViewButton>
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
                Updating <strong>{currentlyLoading[0].id}</strong>
              </span>
            ) : (
              <span>Updating {currentlyLoading.length} code locations</span>
            )}
            <ViewButton onClick={() => history.push('/workspace')} color={Colors.White}>
              View
            </ViewButton>
          </Box>
        ),
        icon: 'refresh',
      });

      return;
    }

    // A location was previously loading, and no longer is. Our workspace is ready. Refetch it.
    if (anyPreviouslyLoading && !anyCurrentlyLoading) {
      reloadWorkspaceLoudly();
    }

    // It's unlikely that we've made it to this point, since being inside this effect should
    // indicate that `data` and `previousData` have differences that would have been handled by
    // the conditionals above.
  }, [data, previousData, reloadWorkspaceQuietly, reloadWorkspaceLoudly, history]);

  if (showSpinner) {
    return (
      <Tooltip content="Loading workspace…" placement="bottom">
        <Spinner purpose="body-text" fillColor={Colors.Gray300} />
      </Tooltip>
    );
  }

  const repoErrors = locationEntries.filter(
    (locationEntry) => locationEntry.locationOrLoadError?.__typename === 'PythonError',
  );

  if (repoErrors.length) {
    return (
      <WarningTooltip
        content={
          <div>{`${repoErrors.length} ${
            repoErrors.length === 1
              ? 'repository location failed to load'
              : 'repository locations failed to load'
          }`}</div>
        }
        position="bottom"
        modifiers={{offset: {enabled: true, options: {offset: [0, 28]}}}}
      >
        <Icon name="warning" color={Colors.Yellow500} />
      </WarningTooltip>
    );
  }

  return <div style={{width: '16px'}} />;
});

const ViewButton = styled(ButtonLink)`
  white-space: nowrap;
`;

const WORKSPACE_UPDATE_CHECK_QUERY = gql`
  query WorkspaceUpdateCheckQuery {
    workspaceOrError {
      __typename
      ... on Workspace {
        locationEntries {
          __typename
          id
          loadStatus
        }
      }
    }
  }
`;
