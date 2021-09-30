import {gql, useQuery} from '@apollo/client';
import {Colors, NonIdealState} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {Box} from '../ui/Box';
import {Group} from '../ui/Group';
import {Table} from '../ui/Table';

import {repoAddressAsString} from './repoAddressAsString';
import {repoAddressToSelector} from './repoAddressToSelector';
import {RepoAddress} from './types';
import {RepositoryGraphsListQuery} from './types/RepositoryGraphsListQuery';
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

export const RepositoryGraphsList: React.FC<Props> = (props) => {
  const {repoAddress} = props;
  const repositorySelector = repoAddressToSelector(repoAddress);

  const {data, error, loading} = useQuery<RepositoryGraphsListQuery>(REPOSITORY_GRAPHS_LIST_QUERY, {
    fetchPolicy: 'cache-and-network',
    variables: {repositorySelector},
  });

  const repo = data?.repositoryOrError;
  const graphsForTable = React.useMemo(() => {
    if (!repo || repo.__typename !== 'Repository') {
      return null;
    }
    const items = repo.pipelines.map((pipeline) => ({
      name: pipeline.name,
      path: `/graphs/${pipeline.name}`,
      description: pipeline.description,
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
      <NonIdealState
        title="Unable to load graphs"
        description={`Could not load graphs for ${repoAddressAsString(repoAddress)}`}
      />
    );
  }

  return (
    <Box margin={{top: 16}}>
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
                  <Link to={workspacePath(repoAddress.name, repoAddress.location, path)}>
                    {name}
                  </Link>
                  <Description>{description}</Description>
                </Group>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Box>
  );
};

const Description = styled.div`
  color: ${Colors.GRAY3};
  font-size: 12px;
`;
