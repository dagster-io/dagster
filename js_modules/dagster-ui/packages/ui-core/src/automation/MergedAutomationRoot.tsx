import {Box, Colors, NonIdealState, Spinner} from '@dagster-io/ui-components';
import {useContext, useMemo} from 'react';

import {AutomationsTable} from './AutomationsTable';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {useSelectionReducer} from '../hooks/useSelectionReducer';
import {filterPermissionedInstigationState} from '../instigation/filterPermissionedInstigationState';
import {sortRepoBuckets} from '../overview/sortRepoBuckets';
import {visibleRepoKeys} from '../overview/visibleRepoKeys';
import {makeAutomationKey} from '../sensors/makeSensorKey';
import {CheckAllBox} from '../ui/CheckAllBox';
import {WorkspaceContext} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {WorkspaceLocationNodeFragment} from '../workspace/types/WorkspaceQueries.types';

export const MergedAutomationRoot = () => {
  useTrackPageView();
  useDocumentTitle('Automation');

  const {
    allRepos,
    visibleRepos,
    loading: workspaceLoading,
    data: cachedData,
  } = useContext(WorkspaceContext);

  const [searchValue] = useQueryPersistedState<string>({
    queryKey: 'search',
    defaults: {search: ''},
  });

  const repoBuckets = useMemo(() => {
    const cachedEntries = Object.values(cachedData).filter(
      (location): location is Extract<typeof location, {__typename: 'WorkspaceLocationEntry'}> =>
        location.__typename === 'WorkspaceLocationEntry',
    );
    const visibleKeys = visibleRepoKeys(visibleRepos);
    return buildBuckets(cachedEntries).filter(({repoAddress}) =>
      visibleKeys.has(repoAddressAsHumanString(repoAddress)),
    );
  }, [cachedData, visibleRepos]);

  const sanitizedSearch = searchValue.trim().toLocaleLowerCase();
  const anySearch = sanitizedSearch.length > 0;

  const filteredBySearch = useMemo(() => {
    const searchToLower = sanitizedSearch.toLocaleLowerCase();
    return repoBuckets
      .map(({repoAddress, schedules, sensors}) => ({
        repoAddress,
        schedules: schedules
          .filter(({name}) => name.toLocaleLowerCase().includes(searchToLower))
          .map(({name}) => name),
        sensors: sensors
          .filter(({name}) => name.toLocaleLowerCase().includes(searchToLower))
          .map(({name}) => name),
      }))
      .filter(({sensors, schedules}) => sensors.length > 0 || schedules.length > 0);
  }, [repoBuckets, sanitizedSearch]);

  // Collect all automations across visible code locations that the viewer has permission
  // to start or stop.
  const allPermissionedAutomations = useMemo(() => {
    return repoBuckets
      .map(({repoAddress, schedules, sensors}) => {
        return [
          ...sensors
            .filter(({sensorState}) => filterPermissionedInstigationState(sensorState))
            .map(({name}) => ({repoAddress, name})),
          ...schedules
            .filter(({scheduleState}) => filterPermissionedInstigationState(scheduleState))
            .map(({name}) => ({repoAddress, name})),
        ];
      })
      .flat();
  }, [repoBuckets]);

  // Build a list of keys from the permissioned schedules for use in checkbox state.
  // This includes collapsed code locations.
  const allPermissionedAutomationKeys = useMemo(() => {
    return allPermissionedAutomations.map(({repoAddress, name}) =>
      makeAutomationKey(repoAddress, name),
    );
  }, [allPermissionedAutomations]);

  const [{checkedIds: checkedKeys}, {onToggleFactory, onToggleAll}] = useSelectionReducer(
    allPermissionedAutomationKeys,
  );

  // Filter to find keys that are visible given any text search.
  const permissionedKeysOnScreen = useMemo(() => {
    const filteredKeys = new Set(
      filteredBySearch
        .map(({repoAddress, schedules, sensors}) => {
          return [...schedules, ...sensors].map((name) => makeAutomationKey(repoAddress, name));
        })
        .flat(),
    );
    return allPermissionedAutomationKeys.filter((key) => filteredKeys.has(key));
  }, [allPermissionedAutomationKeys, filteredBySearch]);

  // Determine the list of sensor objects that have been checked by the viewer.
  // These are the sensors that will be operated on by the bulk start/stop action.
  const checkedAutomations = useMemo(() => {
    const checkedKeysOnScreen = new Set(
      permissionedKeysOnScreen.filter((key: string) => checkedKeys.has(key)),
    );
    return allPermissionedAutomations.filter(({repoAddress, name}) => {
      return checkedKeysOnScreen.has(makeAutomationKey(repoAddress, name));
    });
  }, [permissionedKeysOnScreen, allPermissionedAutomations, checkedKeys]);

  const viewerHasAnyInstigationPermission = allPermissionedAutomationKeys.length > 0;
  const checkedCount = checkedAutomations.length;

  const content = () => {
    if (workspaceLoading) {
      return (
        <Box flex={{direction: 'row', justifyContent: 'center'}} style={{paddingTop: '100px'}}>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
            <Spinner purpose="body-text" />
            <div style={{color: Colors.textLight()}}>Loading automations…</div>
          </Box>
        </Box>
      );
    }

    const anyReposHidden = allRepos.length > visibleRepos.length;

    if (!filteredBySearch.length) {
      if (anySearch) {
        return (
          <Box padding={{top: 20}}>
            <NonIdealState
              icon="search"
              title="No matching automations"
              description={
                anyReposHidden ? (
                  <div>
                    No automations matching <strong>{searchValue}</strong> were found in the
                    selected code locations
                  </div>
                ) : (
                  <div>
                    No automations matching <strong>{searchValue}</strong> were found in your
                    definitions
                  </div>
                )
              }
            />
          </Box>
        );
      }

      return (
        <Box padding={{top: 20}}>
          <NonIdealState
            icon="search"
            title="No automations"
            description={
              anyReposHidden
                ? 'No automations were found in the selected code locations'
                : 'No automations were found in your definitions'
            }
          />
        </Box>
      );
    }

    return (
      <AutomationsTable
        headerCheckbox={
          viewerHasAnyInstigationPermission ? (
            <CheckAllBox
              checkedCount={checkedCount}
              totalCount={permissionedKeysOnScreen.length}
              onToggleAll={onToggleAll}
            />
          ) : undefined
        }
        repos={filteredBySearch}
        checkedKeys={checkedKeys}
        onToggleCheckFactory={onToggleFactory}
      />
    );
  };

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      {content()}
    </Box>
  );
};

const buildBuckets = (
  locationEntries: Extract<WorkspaceLocationNodeFragment, {__typename: 'WorkspaceLocationEntry'}>[],
) => {
  const entries = locationEntries.map((entry) => entry.locationOrLoadError);

  const buckets = [];

  for (const entry of entries) {
    if (entry?.__typename !== 'RepositoryLocation') {
      continue;
    }

    for (const repo of entry.repositories) {
      const {name, schedules, sensors} = repo;
      const repoAddress = buildRepoAddress(name, entry.name);

      if (sensors.length > 0) {
        buckets.push({
          repoAddress,
          schedules,
          sensors,
        });
      }
    }
  }

  return sortRepoBuckets(buckets);
};
