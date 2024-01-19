import {gql, useQuery} from '@apollo/client';
import {
  Box,
  Colors,
  Heading,
  NonIdealState,
  PageHeader,
  Spinner,
  TextInput,
} from '@dagster-io/ui-components';
import * as React from 'react';

import {OverviewResourcesTable} from './OverviewResourcesTable';
import {OverviewTabs} from './OverviewTabs';
import {sortRepoBuckets} from './sortRepoBuckets';
import {
  OverviewResourcesQuery,
  OverviewResourcesQueryVariables,
} from './types/OverviewResourcesRoot.types';
import {visibleRepoKeys} from './visibleRepoKeys';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {RepoFilterButton} from '../instance/RepoFilterButton';
import {RESOURCE_ENTRY_FRAGMENT} from '../resources/WorkspaceResourcesRoot';
import {ResourceEntryFragment} from '../resources/types/WorkspaceResourcesRoot.types';
import {SearchInputSpinner} from '../ui/SearchInputSpinner';
import {WorkspaceContext} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

export const OverviewResourcesRoot = () => {
  useTrackPageView();
  useDocumentTitle('Overview | Resources');

  const {allRepos, visibleRepos, loading: workspaceLoading} = React.useContext(WorkspaceContext);
  const [searchValue, setSearchValue] = useQueryPersistedState<string>({
    queryKey: 'search',
    defaults: {search: ''},
  });

  const repoCount = allRepos.length;

  const queryResultOverview = useQuery<OverviewResourcesQuery, OverviewResourcesQueryVariables>(
    OVERVIEW_RESOURCES_QUERY,
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
      .map(({repoAddress, resources}) => ({
        repoAddress,
        resources: resources.filter(({name}) => name.toLocaleLowerCase().includes(searchToLower)),
      }))
      .filter(({resources}) => resources.length > 0);
  }, [repoBuckets, sanitizedSearch]);

  const content = () => {
    if (loading && !data) {
      return (
        <Box flex={{direction: 'row', justifyContent: 'center'}} style={{paddingTop: '100px'}}>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
            <Spinner purpose="body-text" />
            <div style={{color: Colors.textLight()}}>Loading resources…</div>
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
              title="No matching resources"
              description={
                anyReposHidden ? (
                  <div>
                    No resources matching <strong>{searchValue}</strong> were found in the selected
                    code locations
                  </div>
                ) : (
                  <div>
                    No resources matching <strong>{searchValue}</strong> were found in your
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
            title="No resources"
            description={
              anyReposHidden
                ? 'No resources were found in the selected code locations'
                : 'No resources were found in your definitions'
            }
          />
        </Box>
      );
    }

    return <OverviewResourcesTable repos={filteredBySearch} />;
  };

  const showSearchSpinner = (workspaceLoading && !repoCount) || (loading && !data);

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader
        title={<Heading>Overview</Heading>}
        tabs={<OverviewTabs tab="resources" refreshState={refreshState} />}
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
            showSearchSpinner ? (
              <SearchInputSpinner tooltipContent="Loading resources…" />
            ) : undefined
          }
          onChange={(e) => setSearchValue(e.target.value)}
          placeholder="Filter by resource name…"
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
  resources: ResourceEntryFragment[];
};

const buildBuckets = (data?: OverviewResourcesQuery): RepoBucket[] => {
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
      const {name, allTopLevelResourceDetails} = repo;
      const repoAddress = buildRepoAddress(name, entry.name);

      if (allTopLevelResourceDetails.length > 0) {
        buckets.push({
          repoAddress,
          resources: allTopLevelResourceDetails,
        });
      }
    }
  }

  return sortRepoBuckets(buckets);
};

const OVERVIEW_RESOURCES_QUERY = gql`
  query OverviewResourcesQuery {
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
                allTopLevelResourceDetails {
                  id
                  ...ResourceEntryFragment
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
  ${RESOURCE_ENTRY_FRAGMENT}
`;
