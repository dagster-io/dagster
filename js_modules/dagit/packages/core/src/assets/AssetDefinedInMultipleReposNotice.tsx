import {gql, useQuery} from '@apollo/client';
import {Alert, Box, ButtonLink, Colors} from '@dagster-io/ui';
import React from 'react';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {buildRepoPath} from '../workspace/buildRepoAddress';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

import {AssetKey} from './types';
import {
  AssetDefinitionCollisionQuery,
  AssetDefinitionCollisionQueryVariables,
} from './types/AssetDefinitionCollisionQuery';

export const MULTIPLE_DEFINITIONS_WARNING = 'Multiple asset definitions found';

export const AssetDefinedInMultipleReposNotice: React.FC<{
  assetKey: AssetKey;
  loadedFromRepo: RepoAddress;
  padded?: boolean;
}> = ({assetKey, loadedFromRepo, padded}) => {
  const {data} = useQuery<AssetDefinitionCollisionQuery, AssetDefinitionCollisionQueryVariables>(
    ASSET_DEFINITION_COLLISION_QUERY,
    {variables: {assetKeys: [{path: assetKey.path}]}},
  );

  const collision = data?.assetNodeDefinitionCollisions[0];
  if (!collision) {
    return <span />;
  }

  const allReposWithAsset = collision.repositories.map((r) =>
    repoAddressAsString({name: r.name, location: r.location.name}),
  );

  return (
    <Box
      padding={padded ? {vertical: 16, left: 24, right: 12} : {}}
      border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
    >
      <Alert
        intent="warning"
        title={MULTIPLE_DEFINITIONS_WARNING}
        description={
          <>
            This asset was loaded from {buildRepoPath(loadedFromRepo.name, loadedFromRepo.location)}
            , but duplicate definitions were found in{' '}
            <ButtonLink
              underline="always"
              color={Colors.Yellow700}
              onClick={() =>
                showCustomAlert({
                  title: MULTIPLE_DEFINITIONS_WARNING,
                  body: (
                    <>
                      Repositories containing an asset definition for{' '}
                      <strong>{displayNameForAssetKey(assetKey)}</strong>:
                      <ul>
                        {allReposWithAsset.map((addr) => (
                          <li key={addr}>{addr}</li>
                        ))}
                      </ul>
                    </>
                  ),
                })
              }
            >
              {allReposWithAsset.length - 1} other repo{allReposWithAsset.length === 2 ? '' : 's'}
            </ButtonLink>
            . You should rename these assets to avoid collisions.
          </>
        }
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
