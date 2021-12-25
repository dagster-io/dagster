import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {displayNameForAssetKey} from '../app/Util';
import {PipelineReference} from '../pipelines/PipelineReference';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {NonIdealState} from '../ui/NonIdealState';
import {Table} from '../ui/Table';

import {repoAddressAsString} from './repoAddressAsString';
import {repoAddressToSelector} from './repoAddressToSelector';
import {RepoAddress} from './types';
import {RepositoryAssetsListQuery} from './types/RepositoryAssetsListQuery';

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
          jobs {
            id
            name
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
  const {repoAddress} = props;
  const repositorySelector = repoAddressToSelector(repoAddress);

  const {data, error, loading} = useQuery<RepositoryAssetsListQuery>(REPOSITORY_ASSETS_LIST_QUERY, {
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
                <Link to={`/instance/assets/${asset.assetKey.path.join('/')}`}>
                  {displayNameForAssetKey(asset.assetKey)}
                </Link>
                <Description>{asset.description}</Description>
              </Box>
            </td>
            <td>
              <Box flex={{direction: 'column', gap: 2}}>
                {asset.jobs.map(({name}) => (
                  <PipelineReference
                    showIcon
                    isJob
                    key={name}
                    pipelineName={name}
                    pipelineHrefContext={repoAddress}
                  />
                ))}
              </Box>
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
