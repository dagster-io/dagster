import {gql, useQuery} from '@apollo/client';
import {
  Alert,
  Box,
  Button,
  Colors,
  Dialog,
  DialogFooter,
  Heading,
  NonIdealState,
  PageHeader,
  Spinner,
  TextInput,
} from '@dagster-io/ui';
import * as React from 'react';

import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {useQueryRefreshAtInterval, FIFTEEN_SECONDS} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {RepoFilterButton} from '../instance/RepoFilterButton';
import {INSTIGATION_STATE_FRAGMENT} from '../instigation/InstigationUtils';
import {UnloadableSensors} from '../instigation/Unloadable';
import {WorkspaceContext} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {RepoAddress} from '../workspace/types';

import {OverviewSensorTable} from './OverviewSensorsTable';
import {OverviewTabs} from './OverviewTabs';
import {OverviewSensorsQuery} from './types/OverviewSensorsQuery';
import {UnloadableSchedulesQuery} from './types/UnloadableSchedulesQuery';

export const OverviewSensorsRoot = () => {
  useTrackPageView();

  const [searchValue, setSearchValue] = React.useState('');
  const {allRepos} = React.useContext(WorkspaceContext);
  const repoCount = allRepos.length;

  const queryResultOverview = useQuery<OverviewSensorsQuery>(OVERVIEW_SENSORS_QUERY, {
    fetchPolicy: 'network-only',
    notifyOnNetworkStatusChange: true,
  });
  const {data, loading} = queryResultOverview;

  const refreshState = useQueryRefreshAtInterval(queryResultOverview, FIFTEEN_SECONDS);

  const repoBuckets = useRepoBuckets(data);
  const sanitizedSearch = searchValue.trim().toLocaleLowerCase();
  const anySearch = sanitizedSearch.length > 0;

  const filteredBySearch = React.useMemo(() => {
    const searchToLower = sanitizedSearch.toLocaleLowerCase();
    return repoBuckets
      .map(({repoAddress, sensors}) => ({
        repoAddress,
        sensors: sensors.filter((name) => name.toLocaleLowerCase().includes(searchToLower)),
      }))
      .filter(({sensors}) => sensors.length > 0);
  }, [repoBuckets, sanitizedSearch]);

  const content = () => {
    if (loading && !data) {
      return (
        <Box flex={{direction: 'row', justifyContent: 'center'}} style={{paddingTop: '100px'}}>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
            <Spinner purpose="body-text" />
            <div style={{color: Colors.Gray600}}>Loading sensors…</div>
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
                  No sensors matching <strong>{searchValue}</strong> were found in this workspace
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
            description="No sensors were found in this workspace"
          />
        </Box>
      );
    }

    return <OverviewSensorTable repos={filteredBySearch} />;
  };

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader
        title={<Heading>Overview</Heading>}
        tabs={<OverviewTabs tab="sensors" refreshState={refreshState} />}
      />
      <Box
        padding={{horizontal: 24, vertical: 16}}
        flex={{direction: 'row', alignItems: 'center', gap: 12, grow: 0}}
      >
        {repoCount > 0 ? <RepoFilterButton /> : null}
        <TextInput
          icon="search"
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          placeholder="Filter by sensor name…"
          style={{width: '340px'}}
        />
      </Box>
      {loading && !repoCount ? (
        <Box padding={64}>
          <Spinner purpose="page" />
        </Box>
      ) : (
        <>
          {data?.unloadableInstigationStatesOrError.__typename === 'InstigationStates' ? (
            <UnloadableSensorsAlert
              count={data.unloadableInstigationStatesOrError.results.length}
            />
          ) : null}
          {content()}
        </>
      )}
    </Box>
  );
};

const UnloadableSensorsAlert: React.FC<{
  count: number;
}> = ({count}) => {
  const [isOpen, setIsOpen] = React.useState(false);

  if (!count) {
    return null;
  }

  const title = count === 1 ? '1 unloadable sensor' : `${count} unloadable sensors`;

  return (
    <>
      <Box
        padding={{vertical: 16, horizontal: 24}}
        border={{side: 'top', width: 1, color: Colors.KeylineGray}}
      >
        <Alert
          intent="warning"
          title={title}
          description={
            <Box flex={{direction: 'column', gap: 12, alignItems: 'flex-start'}}>
              <div>
                Sensors were previously started but now cannot be loaded. They may be part of a
                different workspace or from a sensor or repository that no longer exists in code.
                You can turn them off, but you cannot turn them back on.
              </div>
              <Button onClick={() => setIsOpen(true)}>
                {count === 1 ? 'View unloadable sensor' : 'View unloadable sensors'}
              </Button>
            </Box>
          }
        />
      </Box>
      <Dialog
        isOpen={isOpen}
        title="Unloadable schedules"
        style={{width: '90vw', maxWidth: '1200px'}}
      >
        <Box padding={{bottom: 8}}>
          <UnloadableSensorDialog />
        </Box>
        <DialogFooter>
          <Button intent="primary" onClick={() => setIsOpen(false)}>
            Done
          </Button>
        </DialogFooter>
      </Dialog>
    </>
  );
};

const UnloadableSensorDialog: React.FC = () => {
  const {data} = useQuery<UnloadableSchedulesQuery>(UNLOADABLE_SENSORS_QUERY);
  if (!data) {
    return <Spinner purpose="section" />;
  }

  if (data?.unloadableInstigationStatesOrError.__typename === 'InstigationStates') {
    return (
      <UnloadableSensors
        sensorStates={data.unloadableInstigationStatesOrError.results}
        showSubheading={false}
      />
    );
  }

  return <PythonErrorInfo error={data?.unloadableInstigationStatesOrError} />;
};

type RepoBucket = {
  repoAddress: RepoAddress;
  sensors: string[];
};

const useRepoBuckets = (data?: OverviewSensorsQuery): RepoBucket[] => {
  return React.useMemo(() => {
    if (data?.workspaceOrError.__typename !== 'Workspace') {
      return [];
    }

    const entries = data.workspaceOrError.locationEntries.map((entry) => entry.locationOrLoadError);

    const buckets = [];

    for (const entry of entries) {
      if (entry?.__typename !== 'RepositoryLocation') {
        continue;
      }

      for (const repo of entry.repositories) {
        const {name, sensors} = repo;
        const repoAddress = buildRepoAddress(name, entry.name);
        const sensorNames = sensors.map(({name}) => name);

        if (sensorNames.length > 0) {
          buckets.push({
            repoAddress,
            sensors: sensorNames,
          });
        }
      }
    }

    return buckets;
  }, [data]);
};

const OVERVIEW_SENSORS_QUERY = gql`
  query OverviewSensorsQuery {
    workspaceOrError {
      ... on Workspace {
        locationEntries {
          id
          locationOrLoadError {
            ... on RepositoryLocation {
              id
              name
              repositories {
                id
                name
                sensors {
                  id
                  name
                  description
                }
              }
            }
            ...PythonErrorFragment
          }
        }
      }
      ...PythonErrorFragment
    }
    unloadableInstigationStatesOrError(instigationType: SENSOR) {
      ... on InstigationStates {
        results {
          id
        }
      }
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

const UNLOADABLE_SENSORS_QUERY = gql`
  query UnloadableSensorsQuery {
    unloadableInstigationStatesOrError(instigationType: SENSOR) {
      ... on InstigationStates {
        results {
          id
          ...InstigationStateFragment
        }
      }
      ...PythonErrorFragment
    }
  }

  ${INSTIGATION_STATE_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
