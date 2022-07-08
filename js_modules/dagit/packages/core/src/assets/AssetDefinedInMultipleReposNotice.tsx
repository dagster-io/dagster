import {gql, useQuery} from '@apollo/client';
import {Alert, Box, Colors} from '@dagster-io/ui';
import React from 'react';

import {buildRepoPath} from '../workspace/buildRepoAddress';
import {RepoAddress} from '../workspace/types';
import {AssetKey} from './types';

import {AssetIdScanQuery} from './types/AssetIdScanQuery';

export const AssetDefinedInMultipleReposNotice: React.FC<{
  assetKey: AssetKey;
  loadedFromRepo: RepoAddress;
}> = ({assetKey, loadedFromRepo}) => {
  const {data} = useQuery<AssetIdScanQuery>(ASSET_ID_SCAN_QUERY);
  const otherRepos =
    data?.repositoriesOrError.__typename === 'RepositoryConnection'
      ? data.repositoriesOrError.nodes.filter(
          (r) => r.name !== loadedFromRepo.name || r.location.name !== loadedFromRepo.location,
        )
      : [];
  const otherReposWithAsset = otherRepos.filter((r) =>
    r.assetNodes.some(
      (a) => JSON.stringify(a.assetKey) === JSON.stringify(assetKey) && a.opNames.length,
    ),
  );

  if (otherReposWithAsset.length === 0) {
    return <span />;
  }

  return (
    <Box
      padding={{vertical: 16, left: 24, right: 12}}
      border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
    >
      <Alert
        intent="info"
        title={`Multiple repositories in your workspace include assets with this name. Showing the definition from ${buildRepoPath(
          loadedFromRepo.name,
          loadedFromRepo.location,
        )} below. (Also found in ${otherReposWithAsset
          .map((o) => buildRepoPath(o.name, o.location.name))
          .join(', ')}). You may want to consider renaming to avoid collisions.`}
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
          id
          name
          location {
            id
            name
          }
          assetNodes {
            id
            opNames
            assetKey {
              path
            }
          }
        }
      }
    }
  }
`;
