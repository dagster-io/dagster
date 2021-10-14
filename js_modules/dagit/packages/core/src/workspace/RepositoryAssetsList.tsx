import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {NonIdealState} from '../ui/NonIdealState';
import {Table} from '../ui/Table';

import {repoAddressAsString} from './repoAddressAsString';
import {repoAddressToSelector} from './repoAddressToSelector';
import {RepoAddress} from './types';
import {RepositoryAssetsListQuery} from './types/RepositoryAssetsListQuery';
import {workspacePath} from './workspacePath';

const REPOSITORY_ASSETS_LIST_QUERY = gql`
  query RepositoryAssetsListQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      __typename
      ... on Repository {
        id
        assetNodes {
          id
          assetKey {
            path
          }
          opName
          description
          jobName
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

export const RepositoryAssetsList: React.FC<Props> = (props) => {
  const {repoAddress} = props;
  const repositorySelector = repoAddressToSelector(repoAddress);

  const {data, error, loading} = useQuery<RepositoryAssetsListQuery>(REPOSITORY_ASSETS_LIST_QUERY, {
    fetchPolicy: 'cache-and-network',
    variables: {repositorySelector},
  });

  const repo = data?.repositoryOrError;
  const assetsForTable = React.useMemo(() => {
    if (!repo || repo.__typename !== 'Repository') {
      return null;
    }
    const items = repo.assetNodes.map((asset) => ({
      name: asset.assetKey.path.join(' > '),
      path: `/jobs/${asset.jobName}:default/${asset.assetKey.path
        .map(encodeURIComponent)
        .join('/')}`,
      description: asset.description,
      repoAddress,
    }));

    return items.sort((a, b) => a.name.localeCompare(b.name));
  }, [repo, repoAddress]);

  if (loading) {
    return null;
  }

  if (error || !assetsForTable) {
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

  if (!assetsForTable.length) {
    return (
      <Box padding={{vertical: 64}}>
        <NonIdealState
          icon="error"
          title="No assets found"
          description={`No @asset definitions for ${repoAddressAsString(repoAddress)}`}
        />
      </Box>
    );
  }

  return (
    <Table>
      <tbody>
        {assetsForTable.map(({name, description, path, repoAddress}) => (
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
  color: ${ColorsWIP.Gray400};
  font-size: 12px;
`;
