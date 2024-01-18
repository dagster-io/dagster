import * as React from 'react';
import {gql, useQuery} from '@apollo/client';

import {
  Box,
  Heading,
  NonIdealState,
  PageHeader,
  Spinner,
  TextInput,
  colorTextLight,
} from '@dagster-io/ui-components';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {RepoFilterButton} from '../instance/RepoFilterButton';
import {SearchInputSpinner} from '../ui/SearchInputSpinner';
import {WorkspaceContext} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {OverviewJobsTable} from './OverviewJobsTable';
import {OverviewTabs} from './OverviewTabs';
import {sortRepoBuckets} from './sortRepoBuckets';
import {OverviewJobsQuery, OverviewJobsQueryVariables} from './types/OverviewJobsRoot.types';
import {visibleRepoKeys} from './visibleRepoKeys';

export const OverviewJobsRoot = () => {
  useTrackPageView();
  useDocumentTitle('Overview | Jobs');

  const {allRepos, visibleRepos, loading: workspaceLoading} = React.useContext(WorkspaceContext);
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
  const {data, loading} = queryResultOverview;

  const refreshState = useQueryRefreshAtInterval(queryResultOverview, FIFTEEN_SECONDS);

  // Batch up the data and bucket by repo.
  const repoBuckets = React.useMemo(() => {
    const visibleKeys = visibleRepoKeys(visibleRepos);
    return buildBuckets(data).filter(({repoAddress}) =>
      visibleKeys.has(repoAddressAsHumanString(repoAddress)),
    );
  }, [data, visibleRepos]);

  const sanitizedSearch = searchValue.trim().toLocaleLowerCase();
  const anySearch = sanitizedSearch.length > 0;

  const filteredBySearch = React.useMemo(() => {
    const searchToLower = sanitizedSearch.toLocaleLowerCase();
    return repoBuckets
      .map(({repoAddress, jobs}) => ({
        repoAddress,
        jobs: jobs.filter(({name}) => name.toLocaleLowerCase().includes(searchToLower)),
      }))
      .filter(({jobs}) => jobs.length > 0);
  }, [repoBuckets, sanitizedSearch]);

  const content = () => {
    if (loading && !data) {
      return (
        <Box flex={{direction: 'row', justifyContent: 'center'}} style={{paddingTop: '100px'}}>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
            <Spinner purpose="body-text" />
            <div style={{color: colorTextLight()}}>Loading jobs…</div>
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

  const showSearchSpinner = (workspaceLoading && !repoCount) || (loading && !data);

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader
        title={<Heading>Overview</Heading>}
        tabs={<OverviewTabs tab="jobs" refreshState={refreshState} />}
      />
      <Box
        padding={{horizontal: 24, vertical: 16}}
        flex={{direction: 'row', alignItems: 'center', gap: 12, grow: 0}}
      >
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

const buildBuckets = (data?: OverviewJobsQuery): RepoBucket[] => {
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
