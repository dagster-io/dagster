import {Box, Colors, NonIdealState, Spinner, TextInput} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {VirtualizedGraphTable} from './VirtualizedGraphTable';
import {WORSKPACE_GRAPHS_QUERY} from './WorkspaceGraphsQuery';
import {WorkspaceHeader} from './WorkspaceHeader';
import {extractGraphsForRepo} from './extractGraphsForRepo';
import {repoAddressAsHumanString} from './repoAddressAsString';
import {repoAddressToSelector} from './repoAddressToSelector';
import {RepoAddress} from './types';
import {useQuery} from '../apollo-client';
import {
  WorkspaceGraphsQuery,
  WorkspaceGraphsQueryVariables,
} from './types/WorkspaceGraphsQuery.types';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';

export const WorkspaceGraphsRoot = ({repoAddress}: {repoAddress: RepoAddress}) => {
  useTrackPageView();

  const repoName = repoAddressAsHumanString(repoAddress);
  useDocumentTitle(`Graphs: ${repoName}`);

  const selector = repoAddressToSelector(repoAddress);
  const [searchValue, setSearchValue] = useQueryPersistedState<string>({
    queryKey: 'search',
    defaults: {search: ''},
  });

  const queryResultOverview = useQuery<WorkspaceGraphsQuery, WorkspaceGraphsQueryVariables>(
    WORSKPACE_GRAPHS_QUERY,
    {
      fetchPolicy: 'network-only',
      notifyOnNetworkStatusChange: true,
      variables: {selector},
    },
  );
  const {data, loading} = queryResultOverview;
  const refreshState = useQueryRefreshAtInterval(queryResultOverview, FIFTEEN_SECONDS);

  const sanitizedSearch = searchValue.trim().toLocaleLowerCase();
  const anySearch = sanitizedSearch.length > 0;

  const graphs = useMemo(() => {
    const repo = data?.repositoryOrError;
    if (!repo || repo.__typename !== 'Repository') {
      return [];
    }

    return extractGraphsForRepo(repo);
  }, [data]);

  const filteredBySearch = useMemo(() => {
    const searchToLower = sanitizedSearch.toLocaleLowerCase();
    return graphs.filter(({name}) => name.toLocaleLowerCase().includes(searchToLower));
  }, [graphs, sanitizedSearch]);

  const content = () => {
    if (loading && !data) {
      return (
        <Box flex={{direction: 'row', justifyContent: 'center'}} style={{paddingTop: '100px'}}>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
            <Spinner purpose="body-text" />
            <div style={{color: Colors.textLight()}}>Loading graphs…</div>
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
              title="No matching graphs"
              description={
                <div>
                  No graphs matching <strong>{searchValue}</strong> were found in {repoName}
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
            title="No graphs"
            description={`No graphs were found in ${repoName}`}
          />
        </Box>
      );
    }

    return <VirtualizedGraphTable repoAddress={repoAddress} graphs={filteredBySearch} />;
  };

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <WorkspaceHeader repoAddress={repoAddress} tab="graphs" refreshState={refreshState} />
      <Box padding={{horizontal: 24, vertical: 16}}>
        <TextInput
          icon="search"
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          placeholder="Filter by graph name…"
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
