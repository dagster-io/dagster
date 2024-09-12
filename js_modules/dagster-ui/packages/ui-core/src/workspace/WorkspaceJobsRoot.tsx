import {Box, Colors, NonIdealState, Spinner, TextInput} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {VirtualizedJobTable} from './VirtualizedJobTable';
import {useRepository} from './WorkspaceContext/util';
import {WorkspaceHeader} from './WorkspaceHeader';
import {repoAddressAsHumanString} from './repoAddressAsString';
import {repoAddressToSelector} from './repoAddressToSelector';
import {RepoAddress} from './types';
import {WorkspaceJobsQuery, WorkspaceJobsQueryVariables} from './types/WorkspaceJobsRoot.types';
import {gql, useQuery} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';
import {SearchInputSpinner} from '../ui/SearchInputSpinner';

const NO_REPOS_EMPTY_ARR: any[] = [];

export const WorkspaceJobsRoot = ({repoAddress}: {repoAddress: RepoAddress}) => {
  useTrackPageView();

  const repo = useRepository(repoAddress);

  const repoName = repoAddressAsHumanString(repoAddress);
  useDocumentTitle(`Jobs: ${repoName}`);

  const selector = repoAddressToSelector(repoAddress);
  const [searchValue, setSearchValue] = useQueryPersistedState<string>({
    queryKey: 'search',
    defaults: {search: ''},
  });

  const queryResultOverview = useQuery<WorkspaceJobsQuery, WorkspaceJobsQueryVariables>(
    WORKSPACE_JOBS_QUERY,
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

  const jobs = useMemo(() => {
    if (data?.repositoryOrError.__typename === 'Repository') {
      return data.repositoryOrError.pipelines;
    }
    if (repo) {
      return repo.repository.pipelines;
    }
    return NO_REPOS_EMPTY_ARR;
  }, [data, repo]);

  const loading = jobs === NO_REPOS_EMPTY_ARR;

  useBlockTraceUntilTrue('WorkspaceJobs', !loading);

  const filteredBySearch = useMemo(() => {
    const searchToLower = sanitizedSearch.toLocaleLowerCase();
    return jobs.filter(
      ({name}) => !isHiddenAssetGroupJob(name) && name.toLocaleLowerCase().includes(searchToLower),
    );
  }, [jobs, sanitizedSearch]);

  const content = () => {
    if (loading && !data) {
      return (
        <Box flex={{direction: 'row', justifyContent: 'center'}} style={{paddingTop: '100px'}}>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
            <Spinner purpose="body-text" />
            <div style={{color: Colors.textLight()}}>Loading jobs…</div>
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
                  No jobs matching <strong>{searchValue}</strong> were found in {repoName}
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
            description={`No jobs were found in ${repoName}`}
          />
        </Box>
      );
    }

    return <VirtualizedJobTable repoAddress={repoAddress} jobs={filteredBySearch} />;
  };

  const showSearchSpinner = !data && queryLoading;

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <WorkspaceHeader repoAddress={repoAddress} tab="jobs" refreshState={refreshState} />
      <Box padding={{horizontal: 24, vertical: 16}}>
        <TextInput
          icon="search"
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          placeholder="Filter by job name…"
          style={{width: '340px'}}
          rightElement={
            showSearchSpinner ? <SearchInputSpinner tooltipContent="Loading jobs…" /> : undefined
          }
        />
      </Box>
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

const WORKSPACE_JOBS_QUERY = gql`
  query WorkspaceJobsQuery($selector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $selector) {
      ... on Repository {
        id
        name
        pipelines {
          id
          name
          isJob
        }
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
