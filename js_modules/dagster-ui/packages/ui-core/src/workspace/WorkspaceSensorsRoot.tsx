import {Box, Colors, NonIdealState, Spinner, TextInput, Tooltip} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {VirtualizedSensorTable} from './VirtualizedSensorTable';
import {useRepository} from './WorkspaceContext/util';
import {WorkspaceHeader} from './WorkspaceHeader';
import {repoAddressAsHumanString} from './repoAddressAsString';
import {repoAddressToSelector} from './repoAddressToSelector';
import {RepoAddress} from './types';
import {
  WorkspaceSensorsQuery,
  WorkspaceSensorsQueryVariables,
} from './types/WorkspaceSensorsRoot.types';
import {gql, useQuery} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {useSelectionReducer} from '../hooks/useSelectionReducer';
import {filterPermissionedInstigationState} from '../instigation/filterPermissionedInstigationState';
import {BASIC_INSTIGATION_STATE_FRAGMENT} from '../overview/BasicInstigationStateFragment';
import {SensorBulkActionMenu} from '../sensors/SensorBulkActionMenu';
import {makeSensorKey} from '../sensors/makeSensorKey';
import {useFilters} from '../ui/BaseFilters';
import {CheckAllBox} from '../ui/CheckAllBox';
import {useInstigationStatusFilter} from '../ui/Filters/useInstigationStatusFilter';
import {SearchInputSpinner} from '../ui/SearchInputSpinner';

// Reuse this reference to distinguish no sensors case from data is still loading case;
const NO_DATA_EMPTY_ARR: any[] = [];

export const WorkspaceSensorsRoot = ({repoAddress}: {repoAddress: RepoAddress}) => {
  useTrackPageView();

  const repo = useRepository(repoAddress);

  const repoName = repoAddressAsHumanString(repoAddress);
  useDocumentTitle(`Sensors: ${repoName}`);

  const selector = repoAddressToSelector(repoAddress);
  const [searchValue, setSearchValue] = useQueryPersistedState<string>({
    queryKey: 'search',
    defaults: {search: ''},
  });

  const runningStateFilter = useInstigationStatusFilter();
  const filters = useMemo(() => [runningStateFilter], [runningStateFilter]);
  const {button: filterButton, activeFiltersJsx} = useFilters({filters});

  const queryResultOverview = useQuery<WorkspaceSensorsQuery, WorkspaceSensorsQueryVariables>(
    WORKSPACE_SENSORS_QUERY,
    {
      fetchPolicy: 'network-only',
      notifyOnNetworkStatusChange: true,
      variables: {selector},
    },
  );
  const {data, loading: queryLoading} = queryResultOverview;
  const refreshState = useQueryRefreshAtInterval(queryResultOverview, FIFTEEN_SECONDS);

  const sanitizedSearch = searchValue.trim().toLocaleLowerCase();
  const anySearch = sanitizedSearch.length > 0;

  const sensors = useMemo(() => {
    if (data?.repositoryOrError.__typename === 'Repository') {
      return data.repositoryOrError.sensors;
    }
    if (repo) {
      return repo.repository.sensors;
    }
    return NO_DATA_EMPTY_ARR;
  }, [repo, data]);

  const loading = NO_DATA_EMPTY_ARR === sensors;

  const {state: runningState} = runningStateFilter;
  const filteredByRunningState = useMemo(() => {
    return runningState.size
      ? sensors.filter(({sensorState}) => runningState.has(sensorState.status))
      : sensors;
  }, [sensors, runningState]);

  const filteredBySearch = useMemo(() => {
    const searchToLower = sanitizedSearch.toLocaleLowerCase();
    return filteredByRunningState.filter(({name}) =>
      name.toLocaleLowerCase().includes(searchToLower),
    );
  }, [filteredByRunningState, sanitizedSearch]);

  const anySensorsVisible = filteredBySearch.length > 0;

  const permissionedSensors = useMemo(() => {
    return filteredBySearch.filter(({sensorState}) =>
      filterPermissionedInstigationState(sensorState),
    );
  }, [filteredBySearch]);

  const permissionedKeys = useMemo(() => {
    return permissionedSensors.map(({name}) => makeSensorKey(repoAddress, name));
  }, [permissionedSensors, repoAddress]);

  const [{checkedIds: checkedKeys}, {onToggleFactory, onToggleAll}] =
    useSelectionReducer(permissionedKeys);

  const checkedSensors = useMemo(() => {
    return permissionedSensors
      .filter(({name}) => checkedKeys.has(makeSensorKey(repoAddress, name)))
      .map(({name, sensorState}) => {
        return {repoAddress, sensorName: name, sensorState};
      });
  }, [permissionedSensors, checkedKeys, repoAddress]);

  const permissionedCount = permissionedKeys.length;
  const checkedCount = checkedKeys.size;

  const viewerHasAnyInstigationPermission = permissionedKeys.length > 0;

  const content = () => {
    if (loading && !data) {
      return (
        <Box flex={{direction: 'row', justifyContent: 'center'}} style={{paddingTop: '100px'}}>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
            <Spinner purpose="body-text" />
            <div style={{color: Colors.textLight()}}>Loading sensors…</div>
          </Box>
        </Box>
      );
    }

    if (!filteredBySearch.length) {
      if (anySearch) {
        return (
          <Box padding={{top: 20}}>
            <NonIdealState
              icon="search"
              title="No matching sensors"
              description={
                <div>
                  No sensors matching <strong>{searchValue}</strong> were found in {repoName}
                </div>
              }
            />
          </Box>
        );
      }

      return (
        <Box padding={{top: 20}}>
          <NonIdealState
            icon="search"
            title="No sensors"
            description={`No sensors were found in ${repoName}`}
          />
        </Box>
      );
    }

    return (
      <VirtualizedSensorTable
        repoAddress={repoAddress}
        sensors={filteredBySearch}
        headerCheckbox={
          viewerHasAnyInstigationPermission ? (
            <CheckAllBox
              checkedCount={checkedCount}
              totalCount={permissionedCount}
              onToggleAll={onToggleAll}
            />
          ) : undefined
        }
        checkedKeys={checkedKeys}
        onToggleCheckFactory={onToggleFactory}
      />
    );
  };

  const showSearchSpinner = queryLoading && !data;

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <WorkspaceHeader repoAddress={repoAddress} tab="sensors" refreshState={refreshState} />
      <Box padding={{horizontal: 24, vertical: 16}} flex={{justifyContent: 'space-between'}}>
        <Box flex={{direction: 'row', gap: 12}}>
          {filterButton}
          <TextInput
            icon="search"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            placeholder="Filter by sensor name…"
            style={{width: '340px'}}
            rightElement={
              showSearchSpinner ? (
                <SearchInputSpinner tooltipContent="Loading sensors…" />
              ) : undefined
            }
          />
        </Box>
        <Tooltip
          content="You do not have permission to start or stop these sensors"
          canShow={anySensorsVisible && !viewerHasAnyInstigationPermission}
          placement="top-end"
          useDisabledButtonTooltipFix
        >
          <SensorBulkActionMenu sensors={checkedSensors} onDone={() => refreshState.refetch()} />
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
      {loading && !data ? (
        <Box padding={64}>
          <Spinner purpose="page" />
        </Box>
      ) : (
        content()
      )}
    </Box>
  );
};

const WORKSPACE_SENSORS_QUERY = gql`
  query WorkspaceSensorsQuery($selector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $selector) {
      ... on Repository {
        id
        name
        sensors {
          id
          name
          description
          sensorState {
            id
            ...BasicInstigationStateFragment
          }
        }
      }
      ...PythonErrorFragment
    }
  }

  ${BASIC_INSTIGATION_STATE_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
