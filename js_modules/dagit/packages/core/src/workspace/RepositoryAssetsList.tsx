import {gql, useQuery} from '@apollo/client';
import {Box, Colors, NonIdealState, Table} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {useTrackPageView} from '../app/analytics';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {RepositoryLink} from '../nav/RepositoryLink';

import {repoAddressAsString} from './repoAddressAsString';
import {repoAddressToSelector} from './repoAddressToSelector';
import {RepoAddress} from './types';
import {
  RepositoryAssetsListQuery,
  RepositoryAssetsListQueryVariables,
} from './types/RepositoryAssetsListQuery';

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
          opNames
          description
          repository {
            id
            name
            location {
              id
              name
            }
          }
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
  useTrackPageView();

  const {repoAddress} = props;
  const repositorySelector = repoAddressToSelector(repoAddress);

  const {data, error, loading} = useQuery<
    RepositoryAssetsListQuery,
    RepositoryAssetsListQueryVariables
  >(REPOSITORY_ASSETS_LIST_QUERY, {
    fetchPolicy: 'cache-and-network',
    variables: {repositorySelector},
  });

  const repo = data?.repositoryOrError;
  const assetsForTable = React.useMemo(
    () =>
      (repo?.__typename === 'Repository' ? [...repo.assetNodes] : []).sort((a, b) =>
        displayNameForAssetKey(a.assetKey).localeCompare(displayNameForAssetKey(b.assetKey)),
      ),
    [repo],
  );

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
      <thead>
        <tr>
          <th>Asset Key</th>
          <th>Defined In</th>
        </tr>
      </thead>
      <tbody>
        {assetsForTable.map((asset) => (
          <tr key={asset.id}>
            <td>
              <Box flex={{direction: 'column', gap: 4}}>
                <Link to={assetDetailsPathForKey(asset.assetKey)}>
                  {displayNameForAssetKey(asset.assetKey)}
                </Link>
                <Description>{asset.description}</Description>
              </Box>
            </td>
            <td>
              <Box flex={{direction: 'column'}}>
                <RepositoryLink
                  repoAddress={{
                    name: asset.repository.name,
                    location: asset.repository.location.name,
                  }}
                />
              </Box>
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
