import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {METADATA_ENTRY_FRAGMENT} from '../runs/MetadataEntry';
import {Box} from '../ui/Box';
import {Spinner} from '../ui/Spinner';
import {Subheading} from '../ui/Text';
import {assetKeyToString} from '../workspace/asset-graph/Utils';

import {AssetMaterializations} from './AssetMaterializations';
import {AssetNodeDefinition, ASSET_NODE_DEFINITION_FRAGMENT} from './AssetNodeDefinition';
import {
  LatestMaterializationMetadata,
  LATEST_MATERIALIZATION_METADATA_FRAGMENT,
} from './LastMaterializationMetadata';
import {SnapshotWarning, SNAPSHOT_WARNING_ASSET_FRAGMENT} from './SnapshotWarning';
import {AssetKey} from './types';
import {AssetQuery, AssetQueryVariables} from './types/AssetQuery';

interface Props {
  assetKey: AssetKey;
  asOf: string | null;
}

export const AssetView: React.FC<Props> = ({assetKey, asOf}) => {
  useDocumentTitle(`Asset: ${assetKeyToString(assetKey)}`);
  const before = React.useMemo(() => (asOf ? `${Number(asOf) + 1}` : ''), [asOf]);
  const {data, loading} = useQuery<AssetQuery, AssetQueryVariables>(ASSET_QUERY, {
    variables: {
      assetKey: {path: assetKey.path},
      limit: 1,
      before,
    },
  });

  const isPartitioned = !!(
    data?.assetOrError?.__typename === 'Asset' &&
    data?.assetOrError?.assetMaterializations[0]?.partition
  );

  return (
    <div>
      <div>
        {loading && (
          <Box padding={{vertical: 20}}>
            <Spinner purpose="section" />
          </Box>
        )}

        {data?.assetOrError && data.assetOrError.__typename === 'Asset' && (
          <SnapshotWarning asset={data.assetOrError} asOf={asOf} />
        )}
        {data?.assetOrError &&
          data.assetOrError.__typename === 'Asset' &&
          data.assetOrError.definition && (
            <AssetNodeDefinition assetNode={data.assetOrError.definition} />
          )}
        <Box padding={{vertical: 16, horizontal: 24}}>
          <Subheading>
            {isPartitioned ? 'Latest materialized partition' : 'Latest materialization'}
          </Subheading>
        </Box>
        {data?.assetOrError && data.assetOrError.__typename === 'Asset' && (
          <LatestMaterializationMetadata
            latest={data.assetOrError.assetMaterializations[0]}
            asOf={asOf}
          />
        )}
      </div>
      <AssetMaterializations assetKey={assetKey} asOf={asOf} />
    </div>
  );
};

const ASSET_QUERY = gql`
  query AssetQuery($assetKey: AssetKeyInput!, $limit: Int!, $before: String) {
    assetOrError(assetKey: $assetKey) {
      ... on Asset {
        id
        key {
          path
        }
        ...SnapshotWarningAssetFragment

        assetMaterializations(limit: $limit, beforeTimestampMillis: $before) {
          ...LatestMaterializationMetadataFragment
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
  ${METADATA_ENTRY_FRAGMENT}
  ${ASSET_NODE_DEFINITION_FRAGMENT}
  ${LATEST_MATERIALIZATION_METADATA_FRAGMENT}
  ${SNAPSHOT_WARNING_ASSET_FRAGMENT}
`;
