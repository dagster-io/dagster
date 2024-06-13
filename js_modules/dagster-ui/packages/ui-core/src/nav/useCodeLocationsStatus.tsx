import {Box, ButtonLink, Colors} from '@dagster-io/ui-components';
import {useCallback, useContext, useLayoutEffect, useRef, useState} from 'react';
import {useHistory} from 'react-router-dom';
import {atom, useRecoilValue} from 'recoil';
import styled from 'styled-components';

import {showSharedToaster} from '../app/DomUtils';
import {RepositoryLocationLoadStatus} from '../graphql/types';
import {StatusAndMessage} from '../instance/DeploymentStatusType';
import {WorkspaceContext} from '../workspace/WorkspaceContext';
import {CodeLocationStatusQuery} from '../workspace/types/WorkspaceQueries.types';

type LocationStatusEntry = {
  loadStatus: RepositoryLocationLoadStatus;
  id: string;
  name: string;
};

type EntriesById = Record<string, LocationStatusEntry>;

export const codeLocationStatusAtom = atom<CodeLocationStatusQuery | undefined>({
  key: 'codeLocationStatusQuery',
  default: undefined,
});

export const useCodeLocationsStatus = (): StatusAndMessage | null => {
  const {locationEntries, data} = useContext(WorkspaceContext);
  const [previousEntriesById, setPreviousEntriesById] = useState<EntriesById | null>(null);

  const history = useHistory();
  const historyRef = useRef<typeof history>(history);
  historyRef.current = history;

  const [showSpinner, setShowSpinner] = useState(false);

  const onClickViewButton = useCallback(() => {
    historyRef.current.push('/locations');
  }, []);

  // Reload the workspace, but don't toast about it.

  // Reload the workspace, and show a success or error toast upon completion.
  useLayoutEffect(() => {
    const anyErrors = Object.values(data).some(
      (entry) =>
        entry.__typename === 'PythonError' ||
        entry.locationOrLoadError?.__typename === 'PythonError',
    );

    const showViewButton = !alreadyViewingCodeLocations();

    if (anyErrors) {
      showSharedToaster({
        intent: 'warning',
        message: (
          <Box flex={{direction: 'row', justifyContent: 'space-between', gap: 24, grow: 1}}>
            <div>Definitions loaded with errors</div>
            {showViewButton ? <ViewCodeLocationsButton onClick={onClickViewButton} /> : null}
          </Box>
        ),
        icon: 'check_circle',
      });
    }

    const anyLoading = Object.values(data).some(
      (entry) =>
        entry.__typename === 'WorkspaceLocationEntry' &&
        entry.loadStatus === RepositoryLocationLoadStatus.LOADING,
    );
    if (!anyLoading) {
      setShowSpinner(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, onClickViewButton]);

  const codeLocationStatusQueryData = useRecoilValue(codeLocationStatusAtom);

  useLayoutEffect(() => {
    const isFreshPageload = previousEntriesById === null;
    const showViewButton = !alreadyViewingCodeLocations();

    // Given the previous and current code locations, determine whether to show a) a loading spinner
    // and/or b) a toast indicating that a code location is being reloaded.
    const entries =
      codeLocationStatusQueryData?.locationStatusesOrError?.__typename ===
      'WorkspaceLocationStatusEntries'
        ? codeLocationStatusQueryData?.locationStatusesOrError.entries
        : [];

    let hasUpdatedEntries = entries.length !== Object.keys(previousEntriesById || {}).length;

    if (!isFreshPageload && hasUpdatedEntries) {
      showSharedToaster({
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
    const currEntriesById: {[key: string]: LocationStatusEntry} = {};
    entries.forEach((entry) => {
      const previousEntry = previousEntriesById && previousEntriesById[entry.id];
      const entryIsUpdated = !previousEntry || previousEntry.loadStatus !== entry.loadStatus;
      hasUpdatedEntries = hasUpdatedEntries || entryIsUpdated;
      currEntriesById[entry.id] = entryIsUpdated
        ? {
            id: entry.id,
            loadStatus: entry.loadStatus,
            name: entry.name,
          }
        : previousEntry;
    });

    const currentEntries = Object.values(currEntriesById);

    const currentlyLoading = currentEntries.filter(
      ({loadStatus}: LocationStatusEntry) => loadStatus === RepositoryLocationLoadStatus.LOADING,
    );
    const anyCurrentlyLoading = currentlyLoading.length > 0;

    if (hasUpdatedEntries) {
      setPreviousEntriesById(currEntriesById);
    }

    // If this is a fresh pageload and anything is currently loading, show the spinner, but we
    // don't need to reload the workspace because subsequent polls should see that the location
    // has finished loading and therefore trigger a reload.
    if (isFreshPageload) {
      if (anyCurrentlyLoading) {
        setShowSpinner(true);
      }
      return;
    }

    const previousEntries = Object.values(previousEntriesById || {});
    // At least one code location has been removed. Reload, but don't make a big deal about it
    // since this was probably done manually.
    if (previousEntries.length > currentEntries.length) {
      return;
    }

    // We have a new entry, and it has already finished loading. Wow! It's surprisingly fast for it
    // to have finished loading so quickly, but go ahead and indicate that the location has
    // been added, then reload the workspace.
    if (currentEntries.length > previousEntries.length && !currentlyLoading.length) {
      const previousMap = previousEntries.reduce(
        (accum, {id}) => {
          accum[id] = true;
          return accum;
        },
        {} as Record<string, true>,
      );

      // Count the number of new code locations.
      const addedEntries: string[] = [];
      currentEntries.forEach(({id}) => {
        if (!previousMap.hasOwnProperty(id)) {
          addedEntries.push(id);
        }
      });

      const toastContent = () => {
        if (addedEntries.length === 1) {
          const entryId = addedEntries[0]!;
          const locationName = currEntriesById[entryId]?.name;
          // The entry should be in the entry map, but guard against errors just in case.
          return (
            <span>Code location {locationName ? <strong>{locationName}</strong> : ''} added</span>
          );
        }

        return <span>{addedEntries.length} code locations added</span>;
      };

      showSharedToaster({
        intent: 'primary',
        message: (
          <Box flex={{direction: 'row', justifyContent: 'space-between', gap: 24, grow: 1}}>
            {toastContent()}
            {showViewButton ? <ViewCodeLocationsButton onClick={onClickViewButton} /> : null}
          </Box>
        ),
        icon: 'add_circle',
      });

      return;
    }

    const anyPreviouslyLoading = previousEntries.some(
      ({loadStatus}) => loadStatus === RepositoryLocationLoadStatus.LOADING,
    );

    // One or more code locations are updating, so let the user know. We will not refetch the workspace
    // until all code locations are done updating.
    if (!anyPreviouslyLoading && anyCurrentlyLoading) {
      setShowSpinner(true);

      showSharedToaster({
        intent: 'primary',
        message: (
          <Box flex={{direction: 'row', justifyContent: 'space-between', gap: 24, grow: 1}}>
            {currentlyLoading.length === 1 ? (
              <span>
                Updating <strong>{currentlyLoading[0]!.name}</strong>
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [codeLocationStatusQueryData]);

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

const ViewCodeLocationsButton = ({onClick}: {onClick: () => void}) => {
  return (
    <ViewButton onClick={onClick} color={Colors.accentWhite()}>
      View
    </ViewButton>
  );
};

const ViewButton = styled(ButtonLink)`
  white-space: nowrap;
`;
