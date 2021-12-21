import {gql, useQuery} from '@apollo/client';
import React from 'react';
import {Alert} from '../ui/Alert';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {buildRepoPath} from '../workspace/buildRepoAddress';
import {RepoAddress} from '../workspace/types';
import {AssetIdScanQuery} from './types/AssetIdScanQuery';

export const AssetDefinedInMultipleReposNotice: React.FC<{
  assetId: string;
  loadedFromRepo: RepoAddress;
}> = ({assetId, loadedFromRepo}) => {
  const {data} = useQuery<AssetIdScanQuery>(ASSET_ID_SCAN_QUERY);
  const otherRepos =
    data?.repositoriesOrError.__typename === 'RepositoryConnection'
      ? data.repositoriesOrError.nodes.filter(
          (n) =>
            (n.name !== loadedFromRepo.name || n.location.name !== loadedFromRepo.location) &&
            n.assetNodes.some((n) => n.id === assetId),
        )
      : [];

  if (otherRepos.length === 0) {
    return <span />;
  }

  return (
    <Box
      padding={{vertical: 16, horizontal: 24}}
      border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
    >
      <Alert
        intent="info"
        title={`Multiple assets with this name are loaded in your workspace. Showing the definition from ${buildRepoPath(
          loadedFromRepo.name,
          loadedFromRepo.location,
        )} below. (Also found in ${otherRepos
          .map((o) => buildRepoPath(o.name, o.location.name))
          .join(', ')}). You may want to consider renaming an asset if they are separate entities.`}
      />
    </Box>
  );
};

const ASSET_ID_SCAN_QUERY = gql`
  query AssetIdScanQuery {
    repositoriesOrError {
      __typename
      ... on RepositoryConnection {
        nodes {
          name
          location {
            name
          }
          assetNodes {
            id
          }
        }
      }
    }
  }
`;
