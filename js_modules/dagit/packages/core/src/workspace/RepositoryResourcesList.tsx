import {gql, useQuery} from '@apollo/client';
import {Box, Colors, Group, NonIdealState, Table} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {isAssetGroup} from '../asset-graph/Utils';

import {repoAddressAsString} from './repoAddressAsString';
import {repoAddressToSelector} from './repoAddressToSelector';
import {RepoAddress} from './types';
import {
  RepositoryResourcesListQuery,
  RepositoryResourcesListQueryVariables,
} from './types/RepositoryResourcesListQuery';
import {ContextResourceHeader} from '../pipelines/SidebarModeSection';
import {Description} from '../pipelines/Description';
import {ConfigTypeSchema} from '../typeexplorer/ConfigTypeSchema';
import {CONFIG_TYPE_SCHEMA_FRAGMENT} from '../typeexplorer/ConfigTypeSchema';
import {workspacePath} from './workspacePath';

const REPOSITORY_RESOURCES_LIST_QUERY = gql`
  query RepositoryResourcesListQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      __typename
      ... on Repository {
        id
        defaultResources {
          name
          description
          configField {
            configType {
              ...ConfigTypeSchemaFragment
              recursiveConfigTypes {
                ...ConfigTypeSchemaFragment
              }
            }
          }
        }
      }
      ... on RepositoryNotFoundError {
        message
      }
    }
  }

  ${CONFIG_TYPE_SCHEMA_FRAGMENT}
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
export const RepositoryResourcesList: React.FC<Props> = (props) => {
  const {repoAddress} = props;
  const repositorySelector = repoAddressToSelector(repoAddress);

  const {data, error, loading} = useQuery<
    RepositoryResourcesListQuery,
    RepositoryResourcesListQueryVariables
  >(REPOSITORY_RESOURCES_LIST_QUERY, {
    fetchPolicy: 'cache-and-network',
    variables: {repositorySelector},
  });

  const repo = data?.repositoryOrError;
  const resourcesForTable = React.useMemo(() => {
    if (!repo || repo.__typename !== 'Repository') {
      return null;
    }

    return repo.defaultResources.map((resource) => {
      return (
        <div>
          <ContextResourceHeader>{resource.name}</ContextResourceHeader>
          <Description description={resource.description} />
          {resource.configField && (
            <ConfigTypeSchema
              type={resource.configField.configType}
              typesInScope={resource.configField.configType.recursiveConfigTypes}
            />
          )}
        </div>
      );
    });
  }, [repo, repoAddress]);

  if (loading) {
    return null;
  }

  if (error || !resourcesForTable) {
    return (
      <Box padding={{vertical: 64}}>
        <NonIdealState
          icon="error"
          title="Unable to load resources"
          description={`Could not load resources for ${repoAddressAsString(repoAddress)}`}
        />
      </Box>
    );
  }

  return (
    <Table>
      <thead>
        <tr>
          <th>Resources</th>
        </tr>
      </thead>
      <tbody>
        {resourcesForTable.map((content) => (
          <tr key={`${name}-${repoAddressAsString(repoAddress)}`}>
            <td>
              <Group direction="column" spacing={4}>
                {content}
              </Group>
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
};
