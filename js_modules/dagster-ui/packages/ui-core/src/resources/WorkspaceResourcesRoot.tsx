import {gql, useQuery} from '@apollo/client';
import {Box, Colors, NonIdealState, Spinner, TextInput} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {VirtualizedResourceTable} from './VirtualizedResourceTable';
import {
  WorkspaceResourcesQuery,
  WorkspaceResourcesQueryVariables,
} from './types/WorkspaceResourcesRoot.types';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {useBlockTraceOnQueryResult} from '../performance/TraceContext';
import {WorkspaceHeader} from '../workspace/WorkspaceHeader';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

export const WorkspaceResourcesRoot = ({repoAddress}: {repoAddress: RepoAddress}) => {
  useTrackPageView();

  const repoName = repoAddressAsHumanString(repoAddress);
  useDocumentTitle(`Resources: ${repoName}`);

  const [searchValue, setSearchValue] = useQueryPersistedState<string>({
    queryKey: 'search',
    defaults: {search: ''},
  });

  const selector = repoAddressToSelector(repoAddress);

  const queryResultOverview = useQuery<WorkspaceResourcesQuery, WorkspaceResourcesQueryVariables>(
    WORKSPACE_RESOURCES_QUERY,
    {
      fetchPolicy: 'network-only',
      notifyOnNetworkStatusChange: true,
      variables: {selector},
    },
  );
  useBlockTraceOnQueryResult(queryResultOverview, 'WorkspaceResourcesQuery');
  const {data, loading} = queryResultOverview;
  const refreshState = useQueryRefreshAtInterval(queryResultOverview, FIFTEEN_SECONDS);

  const sanitizedSearch = searchValue.trim().toLocaleLowerCase();
  const anySearch = sanitizedSearch.length > 0;

  const resources = useMemo(() => {
    if (data?.repositoryOrError.__typename === 'Repository') {
      return data.repositoryOrError.allTopLevelResourceDetails;
    }
    return [];
  }, [data]);

  const filteredBySearch = useMemo(() => {
    const searchToLower = sanitizedSearch.toLocaleLowerCase();
    return resources.filter(({name}) => name.toLocaleLowerCase().includes(searchToLower));
  }, [resources, sanitizedSearch]);

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

    if (!filteredBySearch.length) {
      if (anySearch) {
        return (
          <Box padding={{top: 20}}>
            <NonIdealState
              icon="search"
              title="No matching resources"
              description={
                <div>
                  No resources matching <strong>{searchValue}</strong> were found in {repoName}
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
            title="No resources"
            description={`No resources were found in ${repoName}`}
          />
        </Box>
      );
    }

    return <VirtualizedResourceTable repoAddress={repoAddress} resources={filteredBySearch} />;
  };

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <WorkspaceHeader repoAddress={repoAddress} tab="resources" refreshState={refreshState} />
      <Box padding={{horizontal: 24, vertical: 16}}>
        <TextInput
          icon="search"
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          placeholder="Filter by resource name…"
          style={{width: '340px'}}
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

export const RESOURCE_ENTRY_FRAGMENT = gql`
  fragment ResourceEntryFragment on ResourceDetails {
    name
    description
    resourceType
    parentResources {
      name
    }
    assetKeysUsing {
      path
    }
    jobsOpsUsing {
      jobName
    }
    schedulesUsing
    sensorsUsing
  }
`;

const WORKSPACE_RESOURCES_QUERY = gql`
  query WorkspaceResourcesQuery($selector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $selector) {
      ... on Repository {
        id
        name
        allTopLevelResourceDetails {
          id
          ...ResourceEntryFragment
        }
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
  ${RESOURCE_ENTRY_FRAGMENT}
`;
