import {Alert, Box, ButtonLink, Colors} from '@dagster-io/ui-components';

import {AssetKey} from './types';
import {gql, useQuery} from '../apollo-client';
import {
  AssetDefinitionCollisionQuery,
  AssetDefinitionCollisionQueryVariables,
} from './types/AssetDefinedInMultipleReposNotice.types';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {buildRepoPathForHuman} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

export const MULTIPLE_DEFINITIONS_WARNING = 'Multiple asset definitions found';
export const ADDITIONAL_REQUIRED_KEYS_WARNING = 'Additional assets will be materialized';

export const AssetDefinedInMultipleReposNotice = ({
  assetKey,
  loadedFromRepo,
  padded,
}: {
  assetKey: AssetKey;
  loadedFromRepo: RepoAddress;
  padded?: boolean;
}) => {
  const queryResult = useQuery<
    AssetDefinitionCollisionQuery,
    AssetDefinitionCollisionQueryVariables
  >(ASSET_DEFINITION_COLLISION_QUERY, {
    variables: {assetKeys: [{path: assetKey.path}]},
    blocking: false,
  });
  const {data} = queryResult;

  const collision = data?.assetNodeDefinitionCollisions[0];
  if (!collision) {
    return <span />;
  }

  const allReposWithAsset = collision.repositories.map((r) =>
    repoAddressAsHumanString({name: r.name, location: r.location.name}),
  );

  return (
    <Box padding={padded ? {vertical: 16, left: 24, right: 12} : {}} border="bottom">
      <Alert
        intent="warning"
        title={MULTIPLE_DEFINITIONS_WARNING}
        description={
          <>
            This asset was loaded from{' '}
            {buildRepoPathForHuman(loadedFromRepo.name, loadedFromRepo.location)}, but duplicate
            definitions were found in{' '}
            <ButtonLink
              underline="always"
              color={Colors.textYellow()}
              onClick={() =>
                showCustomAlert({
                  title: MULTIPLE_DEFINITIONS_WARNING,
                  body: (
                    <>
                      Code locations containing an asset definition for{' '}
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
