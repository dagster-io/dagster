import {gql, useQuery} from '@apollo/client';
import {Alert, Box, Colors} from '@dagster-io/ui';
import React from 'react';

import {buildRepoPath} from '../workspace/buildRepoAddress';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

import {AssetKey} from './types';
import {
  AssetDefinitionCollisionQuery,
  AssetDefinitionCollisionQueryVariables,
} from './types/AssetDefinitionCollisionQuery';

export const AssetDefinedInMultipleReposNotice: React.FC<{
  assetKey: AssetKey;
  loadedFromRepo: RepoAddress;
  padding?: boolean;
}> = ({assetKey, loadedFromRepo, padding}) => {
  const {data} = useQuery<AssetDefinitionCollisionQuery, AssetDefinitionCollisionQueryVariables>(
    ASSET_DEFINITION_COLLISION_QUERY,
    {variables: {assetKeys: [{path: assetKey.path}]}},
  );

  const collision = data?.assetNodeDefinitionCollisions[0];
  if (!collision) {
    return <span />;
  }

  const otherReposWithAsset = collision.repositories.filter(
    (r) =>
      repoAddressAsString({location: r.location.name, name: r.name}) !==
      repoAddressAsString(loadedFromRepo),
  );

  return (
    <Box
      padding={padding ? {vertical: 16, left: 24, right: 12} : {}}
      border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
    >
      <Alert
        intent="info"
        title={`Multiple repositories in your workspace include assets with this name. Showing the definition from ${buildRepoPath(
          loadedFromRepo.name,
          loadedFromRepo.location,
        )} below. (Also found in ${otherReposWithAsset
          .map((o) => buildRepoPath(o.name, o.location.name))
          .join(', ')}). You should rename these assets to avoid collisions.`}
      />
    </Box>
  );
};

const ASSET_DEFINITION_COLLISION_QUERY = gql`
  query AssetDefinitionCollisionQuery($assetKeys: [AssetKeyInput!]!) {
    assetNodeDefinitionCollisions(assetKeys: $assetKeys) {
      assetKey {
        path
      }
      repositories {
        id
        name
        location {
          id
          name
        }
      }
    }
  }
`;
