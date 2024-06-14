import {gql, useQuery} from '@apollo/client';
import {Box, Colors, NonIdealState, Spinner, TextInput} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {VirtualizedBlueprintManagerTable} from './VirtualizedBlueprintManagerTable';
import {
  WorkspaceBlueprintManagersQuery,
  WorkspaceBlueprintManagersQueryVariables,
} from './types/WorkspaceBlueprintManagersRoot.types';
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

export const WorkspaceBlueprintManagersRoot = ({repoAddress}: {repoAddress: RepoAddress}) => {
  useTrackPageView();

  const repoName = repoAddressAsHumanString(repoAddress);
  useDocumentTitle(`BlueprintManagers: ${repoName}`);

  const [searchValue, setSearchValue] = useQueryPersistedState<string>({
    queryKey: 'search',
    defaults: {search: ''},
  });

  const selector = repoAddressToSelector(repoAddress);

  const queryResultOverview = useQuery<
    WorkspaceBlueprintManagersQuery,
    WorkspaceBlueprintManagersQueryVariables
  >(WORKSPACE_BLUEPRINT_MANAGERS_QUERY, {
    fetchPolicy: 'network-only',
    notifyOnNetworkStatusChange: true,
    variables: {selector},
  });
  useBlockTraceOnQueryResult(queryResultOverview, 'WorkspaceBlueprintManagersQuery');
  const {data, loading} = queryResultOverview;
  const refreshState = useQueryRefreshAtInterval(queryResultOverview, FIFTEEN_SECONDS);

  const sanitizedSearch = searchValue.trim().toLocaleLowerCase();
  const anySearch = sanitizedSearch.length > 0;

  const blueprintManagers = useMemo(() => {
    if (data?.repositoryOrError.__typename === 'Repository') {
      return data.repositoryOrError.blueprintManagers.results;
    }
    return [];
  }, [data]);

  const filteredBySearch = useMemo(() => {
    const searchToLower = sanitizedSearch.toLocaleLowerCase();
    return blueprintManagers.filter(({name}) => name.toLocaleLowerCase().includes(searchToLower));
  }, [blueprintManagers, sanitizedSearch]);

  const content = () => {
    if (loading && !data) {
      return (
        <Box flex={{direction: 'row', justifyContent: 'center'}} style={{paddingTop: '100px'}}>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
            <Spinner purpose="body-text" />
            <div style={{color: Colors.textLight()}}>Loading blueprint managers…</div>
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
              title="No matching blueprint managers"
              description={
                <div>
                  No blueprint managers matching <strong>{searchValue}</strong> were found in{' '}
                  {repoName}
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
            title="No blueprint managers"
            description={`No blueprint managers were found in ${repoName}`}
          />
        </Box>
      );
    }

    return (
      <VirtualizedBlueprintManagerTable
        repoAddress={repoAddress}
        blueprintManagers={filteredBySearch}
      />
    );
  };

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <WorkspaceHeader
        repoAddress={repoAddress}
        tab="blueprintManagers"
        refreshState={refreshState}
        queryData={queryResultOverview}
      />
      <Box padding={{horizontal: 24, vertical: 16}}>
        <TextInput
          icon="search"
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          placeholder="Filter by blueprint manager name…"
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

export const BLUEPRINT_MANAGER_FRAGMENT = gql`
  fragment BlueprintManagerFragment on BlueprintManager {
    id
    name
  }
`;

const WORKSPACE_BLUEPRINT_MANAGERS_QUERY = gql`
  query WorkspaceBlueprintManagersQuery($selector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $selector) {
      ... on Repository {
        id
        name
        blueprintManagers {
          results {
            ...BlueprintManagerFragment
          }
        }
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
  ${BLUEPRINT_MANAGER_FRAGMENT}
`;
