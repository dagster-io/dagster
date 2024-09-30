import {
  Body2,
  Box,
  Colors,
  Heading,
  Icon,
  NonIdealState,
  PageHeader,
  SpinnerWithText,
  TextInput,
  Tooltip,
} from '@dagster-io/ui-components';
import {useContext, useMemo} from 'react';

import {AutomationBulkActionMenu} from './AutomationBulkActionMenu';
import {AutomationsTable} from './AutomationsTable';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {useSelectionReducer} from '../hooks/useSelectionReducer';
import {filterPermissionedInstigationState} from '../instigation/filterPermissionedInstigationState';
import {sortRepoBuckets} from '../overview/sortRepoBuckets';
import {visibleRepoKeys} from '../overview/visibleRepoKeys';
import {makeAutomationKey} from '../sensors/makeSensorKey';
import {useFilters} from '../ui/BaseFilters';
import {useStaticSetFilter} from '../ui/BaseFilters/useStaticSetFilter';
import {CheckAllBox} from '../ui/CheckAllBox';
import {useCodeLocationFilter} from '../ui/Filters/useCodeLocationFilter';
import {useInstigationStatusFilter} from '../ui/Filters/useInstigationStatusFilter';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';
import {WorkspaceLocationNodeFragment} from '../workspace/WorkspaceContext/types/WorkspaceQueries.types';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';

type AutomationType = 'schedules' | 'sensors';

const AUTOMATION_TYPE_FILTERS = {
  schedules: {
    label: 'Schedules',
    value: {type: 'schedules', label: 'Schedules'},
    match: ['schedules'],
  },
  sensors: {
    label: 'Sensors',
    value: {type: 'sensors', label: 'Sensors'},
    match: ['sensors'],
  },
};

const ALL_AUTOMATION_VALUES = Object.values(AUTOMATION_TYPE_FILTERS);

export const MergedAutomationRoot = () => {
  useTrackPageView();
  useDocumentTitle('Automation');

  const {
    allRepos,
    visibleRepos,
    loading: workspaceLoading,
    data: cachedData,
    refetch,
  } = useContext(WorkspaceContext);

  const [searchValue, setSearchValue] = useQueryPersistedState<string>({
    queryKey: 'search',
    defaults: {search: ''},
  });

  const [automationTypes, setAutomationTypes] = useQueryPersistedState<Set<AutomationType>>({
    encode: (vals) => ({automationType: vals.size ? Array.from(vals).join(',') : undefined}),
    decode: (qs) => new Set((qs.automationType?.split(',') as AutomationType[]) || []),
  });

  const automationFilterState = useMemo(() => {
    return new Set(
      Array.from(automationTypes).map(
        (type) => AUTOMATION_TYPE_FILTERS[type as AutomationType].value,
      ),
    );
  }, [automationTypes]);

  const codeLocationFilter = useCodeLocationFilter();
  const runningStateFilter = useInstigationStatusFilter();
  const automationTypeFilter = useStaticSetFilter({
    name: 'Automation type',
    allValues: ALL_AUTOMATION_VALUES,
    icon: 'auto_materialize_policy',
    getStringValue: (value) => value.label,
    state: automationFilterState,
    renderLabel: ({value}) => <span>{value.label}</span>,
    onStateChanged: (state) => {
      setAutomationTypes(new Set(Array.from(state).map((value) => value.type as AutomationType)));
    },
  });

  const filters = useMemo(
    () => [codeLocationFilter, runningStateFilter, automationTypeFilter],
    [codeLocationFilter, runningStateFilter, automationTypeFilter],
  );
  const {button: filterButton, activeFiltersJsx} = useFilters({filters});

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

  const {state: runningState} = runningStateFilter;

  const filteredBuckets = useMemo(() => {
    return repoBuckets.map(({sensors, schedules, ...rest}) => {
      return {
        ...rest,
        sensors: sensors.filter(({sensorState}) => {
          if (runningState.size && !runningState.has(sensorState.status)) {
            return false;
          }
          if (automationTypes.size && !automationTypes.has('sensors')) {
            return false;
          }
          return true;
        }),
        schedules: schedules.filter(({scheduleState}) => {
          if (runningState.size && !runningState.has(scheduleState.status)) {
            return false;
          }
          if (automationTypes.size && !automationTypes.has('schedules')) {
            return false;
          }
          return true;
        }),
      };
    });
  }, [repoBuckets, automationTypes, runningState]);

  const sanitizedSearch = searchValue.trim().toLocaleLowerCase();
  const anySearch = sanitizedSearch.length > 0;

  const filteredBySearch = useMemo(() => {
    const searchToLower = sanitizedSearch.toLocaleLowerCase();
    return filteredBuckets
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
  }, [filteredBuckets, sanitizedSearch]);

  // Collect all automations across visible code locations that the viewer has permission
  // to start or stop.
  const allPermissionedAutomations = useMemo(() => {
    return filteredBuckets
      .map(({repoAddress, schedules, sensors}) => {
        return [
          ...sensors
            .filter(({sensorState}) => filterPermissionedInstigationState(sensorState))
            .map(({name, sensorState}) => ({
              repoAddress,
              name,
              type: 'sensor' as const,
              instigationState: sensorState,
            })),
          ...schedules
            .filter(({scheduleState}) => filterPermissionedInstigationState(scheduleState))
            .map(({name, scheduleState}) => ({
              repoAddress,
              name,
              type: 'schedule' as const,
              instigationState: scheduleState,
            })),
        ];
      })
      .flat();
  }, [filteredBuckets]);

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
  const anyAutomationsVisible = permissionedKeysOnScreen.length > 0;

  const content = () => {
    if (workspaceLoading) {
      return (
        <Box flex={{direction: 'row', justifyContent: 'center'}} padding={{top: 64}}>
          <SpinnerWithText label="Loading automations…" />
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
              anyReposHidden ? (
                'No automations were found in the selected code locations'
              ) : (
                <Body2>
                  There are no automations in this deployment.{' '}
                  <a
                    href="https://docs.dagster.io/concepts/automation"
                    target="_blank"
                    rel="noreferrer"
                  >
                    <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                      Learn more about automations
                      <Icon name="open_in_new" color={Colors.linkDefault()} />
                    </Box>
                  </a>
                </Body2>
              )
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
      <PageHeader title={<Heading>Automation</Heading>} />
      <Box
        padding={{horizontal: 24, vertical: 12}}
        flex={{
          direction: 'row',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
          grow: 0,
        }}
      >
        <Box flex={{direction: 'row', gap: 12}}>
          {filterButton}
          <TextInput
            icon="search"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            placeholder="Filter by name…"
            style={{width: '340px'}}
          />
        </Box>
        <Tooltip
          content="You do not have permission to start or stop these schedules"
          canShow={anyAutomationsVisible && !viewerHasAnyInstigationPermission}
          placement="top-end"
          useDisabledButtonTooltipFix
        >
          <AutomationBulkActionMenu automations={checkedAutomations} onDone={() => refetch()} />
        </Tooltip>
      </Box>
      {activeFiltersJsx.length ? (
        <Box
          padding={{vertical: 8, horizontal: 24}}
          border="top-and-bottom"
          flex={{direction: 'row', gap: 8}}
        >
          {activeFiltersJsx}
        </Box>
      ) : null}
      {content()}
    </Box>
  );
};

// eslint-disable-next-line import/no-default-export
export default MergedAutomationRoot;

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

      if (sensors.length > 0 || schedules.length > 0) {
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
