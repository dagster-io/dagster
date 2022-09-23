import {gql, useQuery} from '@apollo/client';
import {Box, Colors, NonIdealState, Spinner, TextInput} from '@dagster-io/ui';
import * as React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {useTrackPageView} from '../app/analytics';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';

import {Graph, VirtualizedGraphTable} from './VirtualizedGraphTable';
import {WorkspaceHeader} from './WorkspaceHeader';
import {repoAddressToSelector} from './repoAddressToSelector';
import {RepoAddress} from './types';
import {WorkspaceGraphsQuery, WorkspaceGraphsQueryVariables} from './types/WorkspaceGraphsQuery';

export const WorkspaceGraphsRoot = ({repoAddress}: {repoAddress: RepoAddress}) => {
  useTrackPageView();

  const [searchValue, setSearchValue] = React.useState('');
  const selector = repoAddressToSelector(repoAddress);

  const queryResultOverview = useQuery<WorkspaceGraphsQuery, WorkspaceGraphsQueryVariables>(
    WROSKPACE_GRAPHS_QUERY,
    {
      fetchPolicy: 'network-only',
      notifyOnNetworkStatusChange: true,
      variables: {selector},
    },
  );
  const {data, loading} = queryResultOverview;

  const sanitizedSearch = searchValue.trim().toLocaleLowerCase();
  const anySearch = sanitizedSearch.length > 0;

  const graphs = React.useMemo(() => {
    const repo = data?.repositoryOrError;
    if (!repo || repo.__typename !== 'Repository') {
      return [];
    }

    const jobGraphNames = new Set<string>(
      repo.pipelines
        .filter((p) => p.isJob && !isHiddenAssetGroupJob(p.name))
        .map((p) => p.graphName),
    );

    const items: Graph[] = Array.from(jobGraphNames).map((graphName) => ({
      name: graphName,
      path: `/graphs/${graphName}`,
      description: null,
    }));

    repo.usedSolids.forEach((s) => {
      if (s.definition.__typename === 'CompositeSolidDefinition') {
        items.push({
          name: s.definition.name,
          path: `/graphs/${s.invocations[0].pipeline.name}/${s.invocations[0].solidHandle.handleID}/`,
          description: s.definition.description,
        });
      }
    });

    return items.sort((a, b) => a.name.localeCompare(b.name));
  }, [data]);

  const filteredBySearch = React.useMemo(() => {
    const searchToLower = sanitizedSearch.toLocaleLowerCase();
    return graphs.filter(({name}) => name.toLocaleLowerCase().includes(searchToLower));
  }, [graphs, sanitizedSearch]);

  const content = () => {
    if (loading && !data) {
      return (
        <Box flex={{direction: 'row', justifyContent: 'center'}} style={{paddingTop: '100px'}}>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
            <Spinner purpose="body-text" />
            <div style={{color: Colors.Gray600}}>Loading graphs…</div>
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
                  No graphs matching <strong>{searchValue}</strong> were found in this repository
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
            description="No graphs were found in this repository"
          />
        </Box>
      );
    }

    return <VirtualizedGraphTable repoAddress={repoAddress} graphs={filteredBySearch} />;
  };

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <WorkspaceHeader repoAddress={repoAddress} tab="graphs" />
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

const WROSKPACE_GRAPHS_QUERY = gql`
  query WorkspaceGraphsQuery($selector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $selector) {
      ... on Repository {
        id
        usedSolids {
          definition {
            __typename
            ... on CompositeSolidDefinition {
              id
              name
              description
            }
          }
          invocations {
            pipeline {
              id
              name
            }
            solidHandle {
              handleID
            }
          }
        }
        pipelines {
          id
          name
          isJob
          graphName
        }
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
