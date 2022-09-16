import {gql, useQuery} from '@apollo/client';
import {Box, Colors, Heading, NonIdealState, PageHeader, Spinner, TextInput} from '@dagster-io/ui';
import * as React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {useTrackPageView} from '../app/analytics';
import {RepoFilterButton} from '../instance/RepoFilterButton';
import {HeaderCell} from '../ui/VirtualizedTable';

import {VirtualizedSensorTable} from './VirtualizedSensorTable';
import {WorkspaceContext} from './WorkspaceContext';
import {WorkspaceTabs} from './WorkspaceTabs';
import {buildRepoAddress} from './buildRepoAddress';
import {RepoAddress} from './types';
import {WorkspaceSensorsQuery} from './types/WorkspaceSensorsQuery';

export const WorkspaceSensorsRoot = () => {
  useTrackPageView();

  const [searchValue, setSearchValue] = React.useState('');
  const {allRepos} = React.useContext(WorkspaceContext);
  const repoCount = allRepos.length;

  const queryResultOverview = useQuery<WorkspaceSensorsQuery>(WORKSPACE_SENSORS_QUERY, {
    fetchPolicy: 'network-only',
    notifyOnNetworkStatusChange: true,
  });
  const {data, loading} = queryResultOverview;

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

  console.log(filteredBySearch);

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

    return (
      <>
        <Box
          border={{side: 'horizontal', width: 1, color: Colors.KeylineGray}}
          style={{
            display: 'grid',
            gridTemplateColumns: '76px 38% 30% 10% 20%',
            height: '32px',
            fontSize: '12px',
            color: Colors.Gray600,
          }}
        >
          <HeaderCell />
          <HeaderCell>Sensor name</HeaderCell>
          <HeaderCell>Frequency</HeaderCell>
          <HeaderCell>Last tick</HeaderCell>
          <HeaderCell>Last run</HeaderCell>
        </Box>
        <div style={{overflow: 'hidden'}}>
          <VirtualizedSensorTable repos={filteredBySearch} />
        </div>
      </>
    );
  };

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader title={<Heading>Workspace</Heading>} tabs={<WorkspaceTabs tab="sensors" />} />
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
        content()
      )}
    </Box>
  );
};

type RepoBucket = {
  repoAddress: RepoAddress;
  sensors: string[];
};

const useRepoBuckets = (data?: WorkspaceSensorsQuery): RepoBucket[] => {
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

const WORKSPACE_SENSORS_QUERY = gql`
  query WorkspaceSensorsQuery {
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
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
