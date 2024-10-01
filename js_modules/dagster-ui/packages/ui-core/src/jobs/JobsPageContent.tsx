import {
  Box,
  Colors,
  NonIdealState,
  Spinner,
  SpinnerWithText,
  TextInput,
} from '@dagster-io/ui-components';
import {useContext, useMemo} from 'react';

import {OverviewJobsQuery, OverviewJobsQueryVariables} from './types/JobsPageContent.types';
import {gql, useQuery} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {RepoFilterButton} from '../instance/RepoFilterButton';
import {OverviewJobsTable} from '../overview/OverviewJobsTable';
import {sortRepoBuckets} from '../overview/sortRepoBuckets';
import {visibleRepoKeys} from '../overview/visibleRepoKeys';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';
import {SearchInputSpinner} from '../ui/SearchInputSpinner';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';
import {WorkspaceLocationNodeFragment} from '../workspace/WorkspaceContext/types/WorkspaceQueries.types';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

export const JobsPageContent = () => {
  const {
    allRepos,
    visibleRepos,
    loading: workspaceLoading,
    data: cachedData,
  } = useContext(WorkspaceContext);
  const [searchValue, setSearchValue] = useQueryPersistedState<string>({
    queryKey: 'search',
    defaults: {search: ''},
  });

  const repoCount = allRepos.length;

  const queryResultOverview = useQuery<OverviewJobsQuery, OverviewJobsQueryVariables>(
    OVERVIEW_JOBS_QUERY,
    {
      fetchPolicy: 'network-only',
      notifyOnNetworkStatusChange: true,
    },
  );
  const {data, loading: queryLoading} = queryResultOverview;

  const refreshState = useQueryRefreshAtInterval(queryResultOverview, FIFTEEN_SECONDS);

  // Batch up the data and bucket by repo.
  const repoBuckets = useMemo(() => {
    const cachedEntries = Object.values(cachedData).filter(
      (location): location is Extract<typeof location, {__typename: 'WorkspaceLocationEntry'}> =>
        location.__typename === 'WorkspaceLocationEntry',
    );
    const workspaceOrError = data?.workspaceOrError;
    const entries =
      workspaceOrError?.__typename === 'Workspace'
        ? workspaceOrError.locationEntries
        : cachedEntries;
    const visibleKeys = visibleRepoKeys(visibleRepos);
    return buildBuckets(entries).filter(({repoAddress}) =>
      visibleKeys.has(repoAddressAsHumanString(repoAddress)),
    );
  }, [cachedData, data, visibleRepos]);

  const loading = !data && workspaceLoading;

  useBlockTraceUntilTrue('OverviewJobs', !loading);

  const sanitizedSearch = searchValue.trim().toLocaleLowerCase();
  const anySearch = sanitizedSearch.length > 0;

  const filteredBySearch = useMemo(() => {
    const searchToLower = sanitizedSearch.toLocaleLowerCase();
    return repoBuckets
      .map(({repoAddress, jobs}) => ({
        repoAddress,
        jobs: jobs.filter(({name}) => name.toLocaleLowerCase().includes(searchToLower)),
      }))
      .filter(({jobs}) => jobs.length > 0);
  }, [repoBuckets, sanitizedSearch]);

  const content = () => {
    if (loading) {
      return (
        <Box flex={{direction: 'row', justifyContent: 'center'}} style={{paddingTop: '100px'}}>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
            <Spinner purpose="body-text" />
            <div style={{color: Colors.textLight()}}>Loading jobs…</div>
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
              title="No matching jobs"
              description={
                anyReposHidden ? (
                  <div>
                    No jobs matching <strong>{searchValue}</strong> were found in the selected code
                    locations
                  </div>
                ) : (
                  <div>
                    No jobs matching <strong>{searchValue}</strong> were found in your definitions
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
            title="No jobs"
            description={
              anyReposHidden
                ? 'No jobs were found in the selected code locations'
                : 'No jobs were found in your definitions'
            }
          />
        </Box>
      );
    }

    return <OverviewJobsTable repos={filteredBySearch} />;
  };

  const showSearchSpinner = queryLoading && !data;

  return (
    <>
      <Box
        padding={{horizontal: 24, vertical: 12}}
        flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between', grow: 0}}
      >
        <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
          {repoCount > 1 ? <RepoFilterButton /> : null}
          <TextInput
            icon="search"
            value={searchValue}
            rightElement={
              showSearchSpinner ? <SearchInputSpinner tooltipContent="Loading jobs…" /> : undefined
            }
            onChange={(e) => setSearchValue(e.target.value)}
            placeholder="Filter by job name…"
            style={{width: '340px'}}
          />
        </Box>
        <QueryRefreshCountdown refreshState={refreshState} />
      </Box>
      {loading && !repoCount ? (
        <Box padding={64}>
          <SpinnerWithText label="Loading jobs…" />
        </Box>
      ) : (
        content()
      )}
    </>
  );
};

type RepoBucket = {
  repoAddress: RepoAddress;
  jobs: {
    isJob: boolean;
    name: string;
  }[];
};

const buildBuckets = (
  locationEntries:
    | Extract<OverviewJobsQuery['workspaceOrError'], {__typename: 'Workspace'}>['locationEntries']
    | Extract<WorkspaceLocationNodeFragment, {__typename: 'WorkspaceLocationEntry'}>[],
): RepoBucket[] => {
  const entries = locationEntries.map((entry) => entry.locationOrLoadError);
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

  return sortRepoBuckets(buckets);
};

const OVERVIEW_JOBS_QUERY = gql`
  query OverviewJobsQuery {
    workspaceOrError {
      ... on Workspace {
        id
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
