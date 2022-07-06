import {gql, useQuery} from '@apollo/client';
import {Box, Colors, Group, NonIdealState, Table} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {useTrackPageView} from '../app/analytics';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';

import {repoAddressAsString} from './repoAddressAsString';
import {repoAddressToSelector} from './repoAddressToSelector';
import {RepoAddress} from './types';
import {
  RepositoryGraphsListQuery,
  RepositoryGraphsListQueryVariables,
} from './types/RepositoryGraphsListQuery';
import {workspacePath} from './workspacePath';

const REPOSITORY_GRAPHS_LIST_QUERY = gql`
  query RepositoryGraphsListQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      __typename
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
          description
          name
          isJob
          graphName
        }
      }
      ... on RepositoryNotFoundError {
        message
      }
    }
  }
`;

interface Props {
  repoAddress: RepoAddress;
}

interface Item {
  name: string;
  description: string | null;
  path: string;
  repoAddress: RepoAddress;
}

export const RepositoryGraphsList: React.FC<Props> = (props) => {
  useTrackPageView();

  const {repoAddress} = props;
  const repositorySelector = repoAddressToSelector(repoAddress);

  const {data, error, loading} = useQuery<
    RepositoryGraphsListQuery,
    RepositoryGraphsListQueryVariables
  >(REPOSITORY_GRAPHS_LIST_QUERY, {
    fetchPolicy: 'cache-and-network',
    variables: {repositorySelector},
  });

  const repo = data?.repositoryOrError;
  const graphsForTable = React.useMemo(() => {
    if (!repo || repo.__typename !== 'Repository') {
      return null;
    }
    const jobGraphNames = new Set<string>(
      repo.pipelines
        .filter((p) => p.isJob && !isHiddenAssetGroupJob(p.name))
        .map((p) => p.graphName),
    );
    const items: Item[] = Array.from(jobGraphNames).map((graphName) => ({
      name: graphName,
      path: `/graphs/${graphName}`,
      description: null,
      repoAddress,
    }));

    repo.usedSolids.forEach((s) => {
      if (s.definition.__typename === 'CompositeSolidDefinition') {
        items.push({
          name: s.definition.name,
          path: `/graphs/${s.invocations[0].pipeline.name}/${s.invocations[0].solidHandle.handleID}/`,
          description: s.definition.description,
          repoAddress,
        });
      }
    });

    return items.sort((a, b) => a.name.localeCompare(b.name));
  }, [repo, repoAddress]);

  if (loading) {
    return null;
  }

  if (error || !graphsForTable) {
    return (
      <Box padding={{vertical: 64}}>
        <NonIdealState
          icon="error"
          title="Unable to load graphs"
          description={`Could not load graphs for ${repoAddressAsString(repoAddress)}`}
        />
      </Box>
    );
  }

  if (!graphsForTable.length) {
    return (
      <Box padding={64}>
        <NonIdealState
          icon="schema"
          title="No graphs found"
          description={<div>This repository does not have any graphs defined.</div>}
        />
      </Box>
    );
  }

  return (
    <Table>
      <thead>
        <tr>
          <th>Graph</th>
        </tr>
      </thead>
      <tbody>
        {graphsForTable.map(({name, description, path, repoAddress}) => (
          <tr key={`${name}-${repoAddressAsString(repoAddress)}`}>
            <td>
              <Group direction="column" spacing={4}>
                <Link to={workspacePath(repoAddress.name, repoAddress.location, path)}>{name}</Link>
                <Description>{description}</Description>
              </Group>
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
};

const Description = styled.div`
  color: ${Colors.Gray400};
  font-size: 12px;
`;
