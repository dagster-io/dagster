import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {Box} from '../ui/Box';
import {Spinner} from '../ui/Spinner';
import {assetKeyToString} from '../workspace/asset-graph/Utils';

import {AssetMaterializations} from './AssetMaterializations';
import {AssetNodeDefinition, ASSET_NODE_DEFINITION_FRAGMENT} from './AssetNodeDefinition';
import {AssetKey} from './types';
import {AssetQuery, AssetQueryVariables} from './types/AssetQuery';

interface Props {
  assetKey: AssetKey;
}

export const AssetView: React.FC<Props> = ({assetKey}) => {
  useDocumentTitle(`Asset: ${assetKeyToString(assetKey)}`);

  const {data, loading} = useQuery<AssetQuery, AssetQueryVariables>(ASSET_QUERY, {
    variables: {
      assetKey: {path: assetKey.path},
    },
  });

  return (
    <div>
      <div>
        {loading && (
          <Box
            style={{height: 390}}
            flex={{direction: 'row', justifyContent: 'center', alignItems: 'center'}}
          >
            <Spinner purpose="section" />
          </Box>
        )}

        {/* {data?.assetOrError && data.assetOrError.__typename === 'Asset' && (
          <SnapshotWarning asset={data.assetOrError} asOf={asOf} />
        )} */}
        {data?.assetOrError &&
          data.assetOrError.__typename === 'Asset' &&
          data.assetOrError.definition && (
            <AssetNodeDefinition assetNode={data.assetOrError.definition} />
          )}
      </div>
      <AssetMaterializations assetKey={assetKey} />
    </div>
  );
};

const ASSET_QUERY = gql`
  query AssetQuery($assetKey: AssetKeyInput!) {
    assetOrError(assetKey: $assetKey) {
      ... on Asset {
        id
        key {
          path
        }

        definition {
          id
          description
          opName
          jobName

          ...AssetNodeDefinitionFragment
        }
      }
    }
  }
  ${ASSET_NODE_DEFINITION_FRAGMENT}
`;
