import {gql, useQuery} from '@apollo/client';
import {Box, Colors, Heading, NonIdealState, PageHeader, Spinner, TextInput} from '@dagster-io/ui';
import * as React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {useTrackPageView} from '../app/analytics';
import {RepoFilterButton} from '../instance/RepoFilterButton';
import {HeaderCell} from '../ui/VirtualizedTable';

import {VirtualizedScheduleTable} from './VirtualizedScheduleTable';
import {WorkspaceContext} from './WorkspaceContext';
import {WorkspaceTabs} from './WorkspaceTabs';
import {buildRepoAddress} from './buildRepoAddress';
import {RepoAddress} from './types';
import {WorkspaceSchedulesQuery} from './types/WorkspaceSchedulesQuery';

export const WorkspaceSchedulesRoot = () => {
  useTrackPageView();

  const [searchValue, setSearchValue] = React.useState('');
  const {allRepos} = React.useContext(WorkspaceContext);
  const repoCount = allRepos.length;

  const queryResultOverview = useQuery<WorkspaceSchedulesQuery>(WORKSPACE_SCHEDULES_QUERY, {
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
      .map(({repoAddress, schedules}) => ({
        repoAddress,
        schedules: schedules.filter((name) => name.toLocaleLowerCase().includes(searchToLower)),
      }))
      .filter(({schedules}) => schedules.length > 0);
  }, [repoBuckets, sanitizedSearch]);

  const content = () => {
    if (loading && !data) {
      return (
        <Box flex={{direction: 'row', justifyContent: 'center'}} style={{paddingTop: '100px'}}>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
            <Spinner purpose="body-text" />
            <div style={{color: Colors.Gray600}}>Loading schedules…</div>
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
              title="No matching schedules"
              description={
                <div>
                  No schedules matching <strong>{searchValue}</strong> were found in this workspace
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
            title="No schedules"
            description="No schedules were found in this workspace"
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
            gridTemplateColumns: '76px 28% 30% 10% 20% 10%',
            height: '32px',
            fontSize: '12px',
            color: Colors.Gray600,
          }}
        >
          <HeaderCell />
          <HeaderCell>Job name</HeaderCell>
          <HeaderCell>Schedule</HeaderCell>
          <HeaderCell>Last tick</HeaderCell>
          <HeaderCell>Last run</HeaderCell>
          <HeaderCell>Actions</HeaderCell>
        </Box>
        <div style={{overflow: 'hidden'}}>
          <VirtualizedScheduleTable repos={filteredBySearch} />
        </div>
      </>
    );
  };

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader title={<Heading>Workspace</Heading>} tabs={<WorkspaceTabs tab="schedules" />} />
      <Box
        padding={{horizontal: 24, vertical: 16}}
        flex={{direction: 'row', alignItems: 'center', gap: 12, grow: 0}}
      >
        {repoCount > 0 ? <RepoFilterButton /> : null}
        <TextInput
          icon="search"
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          placeholder="Filter by schedule name…"
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
  schedules: string[];
};

const useRepoBuckets = (data?: WorkspaceSchedulesQuery): RepoBucket[] => {
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
        const {name, schedules} = repo;
        const repoAddress = buildRepoAddress(name, entry.name);
        const scheduleNames = schedules.map(({name}) => name);

        if (scheduleNames.length > 0) {
          buckets.push({
            repoAddress,
            schedules: scheduleNames,
          });
        }
      }
    }

    return buckets;
  }, [data]);
};

const WORKSPACE_SCHEDULES_QUERY = gql`
  query WorkspaceSchedulesQuery {
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
                schedules {
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
