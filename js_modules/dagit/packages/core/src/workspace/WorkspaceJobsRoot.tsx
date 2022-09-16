import {gql, useQuery} from '@apollo/client';
import {Box, Colors, Heading, NonIdealState, PageHeader, Spinner, TextInput} from '@dagster-io/ui';
import * as React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {useTrackPageView} from '../app/analytics';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {RepoFilterButton} from '../instance/RepoFilterButton';
import {RUN_TIME_FRAGMENT} from '../runs/RunUtils';
import {HeaderCell} from '../ui/VirtualizedTable';

import {VirtualizedJobTable} from './VirtualizedJobTable';
import {WorkspaceContext} from './WorkspaceContext';
import {WorkspaceTabs} from './WorkspaceTabs';
import {buildRepoAddress} from './buildRepoAddress';
import {repoAddressAsString} from './repoAddressAsString';
import {RepoAddress} from './types';
import {WorkspaceJobsQuery} from './types/WorkspaceJobsQuery';

export const WorkspaceJobsRoot = () => {
  useTrackPageView();

  const [searchValue, setSearchValue] = React.useState('');
  const {allRepos, visibleRepos} = React.useContext(WorkspaceContext);
  const repoCount = allRepos.length;

  const queryResultOverview = useQuery<WorkspaceJobsQuery>(WORKSPACE_JOBS_QUERY, {
    fetchPolicy: 'network-only',
    notifyOnNetworkStatusChange: true,
  });
  const {data, loading} = queryResultOverview;

  // Batch up the data and bucket by repo.
  const repoBuckets = useRepoBuckets(data);

  const sanitizedSearch = searchValue.trim().toLocaleLowerCase();
  const anySearch = sanitizedSearch.length > 0;

  const filteredRepoBuckets = React.useMemo(() => {
    const visibleRepoKeys = new Set(
      visibleRepos.map((option) =>
        repoAddressAsString(
          buildRepoAddress(option.repository.name, option.repositoryLocation.name),
        ),
      ),
    );
    return repoBuckets.filter(({repoAddress}) =>
      visibleRepoKeys.has(repoAddressAsString(repoAddress)),
    );
  }, [repoBuckets, visibleRepos]);

  const filteredBySearch = React.useMemo(() => {
    const searchToLower = sanitizedSearch.toLocaleLowerCase();
    return filteredRepoBuckets
      .map(({repoAddress, jobs}) => ({
        repoAddress,
        jobs: jobs.filter(({name}) => name.toLocaleLowerCase().includes(searchToLower)),
      }))
      .filter(({jobs}) => jobs.length > 0);
  }, [filteredRepoBuckets, sanitizedSearch]);

  const content = () => {
    if (loading && !data) {
      return (
        <Box flex={{direction: 'row', justifyContent: 'center'}} style={{paddingTop: '100px'}}>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
            <Spinner purpose="body-text" />
            <div style={{color: Colors.Gray600}}>Loading jobs…</div>
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
              title="No matching jobs"
              description={
                <div>
                  No jobs matching <strong>{searchValue}</strong> were found in this workspace
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
            title="No jobs"
            description="No jobs were found in this workspace"
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
            gridTemplateColumns: '34% 30% 20% 8% 8%',
            height: '32px',
            fontSize: '12px',
            color: Colors.Gray600,
          }}
        >
          <HeaderCell>Job name</HeaderCell>
          <HeaderCell>Schedules/sensors</HeaderCell>
          <HeaderCell>Latest run</HeaderCell>
          <HeaderCell>Run history</HeaderCell>
          <HeaderCell>Actions</HeaderCell>
        </Box>
        <div style={{overflow: 'hidden'}}>
          <VirtualizedJobTable repos={filteredBySearch} />
        </div>
      </>
    );
  };

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader title={<Heading>Workspace</Heading>} tabs={<WorkspaceTabs tab="jobs" />} />
      <Box
        padding={{horizontal: 24, vertical: 16}}
        flex={{direction: 'row', alignItems: 'center', gap: 12, grow: 0}}
      >
        {repoCount > 1 ? <RepoFilterButton /> : null}
        <TextInput
          icon="search"
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          placeholder="Filter by job name…"
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
  jobs: {
    isJob: boolean;
    name: string;
  }[];
};

const useRepoBuckets = (data?: WorkspaceJobsQuery): RepoBucket[] => {
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
        const {name, pipelines} = repo;
        const repoAddress = buildRepoAddress(name, entry.name);
        const jobs = pipelines
          .filter(({name}) => !isHiddenAssetGroupJob(name))
          .map((pipeline) => {
            return {
              isJob: pipeline.isJob,
              name: pipeline.name,
            };
          });

        if (jobs.length > 0) {
          buckets.push({
            repoAddress,
            jobs,
          });
        }
      }
    }

    return buckets;
  }, [data]);
};

export const WORKSPACE_JOBS_QUERY = gql`
  query WorkspaceJobsQuery {
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
                pipelines {
                  id
                  name
                  isJob
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

export const RECENT_RUNS_PER_JOB_QUERY = gql`
  query RecentRunsPerJobQuery {
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
                pipelines {
                  id
                  name
                  isJob
                  runs(limit: 5) {
                    id
                    ...RunTimeFragment
                  }
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
  ${RUN_TIME_FRAGMENT}
`;
