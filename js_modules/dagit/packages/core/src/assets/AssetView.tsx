import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {Box} from '../ui/Box';
import {Group} from '../ui/Group';
import {Spinner} from '../ui/Spinner';
import {Subheading} from '../ui/Text';
import {assetKeyToString} from '../workspace/asset-graph/Utils';

import {AssetMaterializations} from './AssetMaterializations';
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
  // const staticContent = () => {
  //   const assetNodeOrError = data?.assetNodeOrError;
  //   if (!assetNodeOrError || assetNodeOrError.__typename !== 'AssetNode') {
  //     return null;
  //   }
  //   return (
  //     <div>
  //       <Description description={assetNodeOrError.description} />
  //     </div>
  //   );
  // };

  const isPartitioned = !!(
    data?.assetOrError?.__typename === 'Asset' &&
    data?.assetOrError?.assetMaterializations[0]?.partition
  );

  return (
    <Group spacing={24} direction="column">
      <Group spacing={16} direction="column">
        {loading && (
          <Box padding={{vertical: 20}}>
            <Spinner purpose="section" />
          </Box>
        )}

        {data?.assetOrError && data.assetOrError.__typename === 'Asset' && (
          <SnapshotWarning asset={data.assetOrError} asOf={asOf} />
        )}
        <Subheading>
          {isPartitioned ? 'Latest Materialized Partition' : 'Latest Materialization'}
        </Subheading>
        {data?.assetOrError && data.assetOrError.__typename === 'Asset' && (
          <LatestMaterializationMetadata
            asset={data.assetOrError.assetMaterializations[0]}
            asOf={asOf}
          />
        )}
      </Group>
      <AssetMaterializations assetKey={assetKey} asOf={asOf} />
    </Group>
  );
};

export const ASSET_QUERY = gql`
  query AssetQuery($assetKey: AssetKeyInput!, $limit: Int!, $before: String) {
    assetNodeOrError(assetKey: $assetKey) {
      ... on AssetNode {
        description
        opName
        jobName
      }

      ... on AssetNotFoundError {
        message
      }
    }

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
      }
    }
  }
  ${LATEST_MATERIALIZATION_METADATA_FRAGMENT}
  ${SNAPSHOT_WARNING_ASSET_FRAGMENT}
`;
