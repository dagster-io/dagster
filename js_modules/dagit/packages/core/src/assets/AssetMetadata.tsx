import {gql} from '@apollo/client';
import {Box, MetadataTable} from '@dagster-io/ui';
import * as React from 'react';

import {DAGSTER_TYPE_FRAGMENT} from '../dagstertype/DagsterType';
import {DagsterTypeFragment} from '../dagstertype/types/DagsterTypeFragment';
import {MetadataEntry, METADATA_ENTRY_FRAGMENT} from '../metadata/MetadataEntry';
import {MetadataEntryFragment} from '../metadata/types/MetadataEntryFragment';

import {AssetNodeOpMetadataFragment} from './types/AssetNodeOpMetadataFragment';

export const metadataForAssetNode = (
  assetNode: AssetNodeOpMetadataFragment,
): {assetType?: DagsterTypeFragment; assetMetadata: MetadataEntryFragment[]} => {
  const assetType = assetNode.op?.outputDefinitions[0]?.type;
  const assetMetadata = assetNode.metadataEntries || [];
  return {assetType, assetMetadata};
};

export const AssetMetadataTable: React.FC<{
  assetMetadata: MetadataEntryFragment[];
}> = ({assetMetadata}) => {
  const rows = assetMetadata.map((entry) => {
    return {
      key: entry.label,
      value: <MetadataEntry entry={entry} />,
    };
  });
  return (
    <Box padding={{vertical: 16, horizontal: 24}}>
      <MetadataTable rows={rows} />
    </Box>
  );
};

export const ASSET_NODE_OP_METADATA_FRAGMENT = gql`
  fragment AssetNodeOpMetadataFragment on AssetNode {
    id
    metadataEntries {
      ...MetadataEntryFragment
    }
    op {
      outputDefinitions {
        type {
          ...DagsterTypeFragment
        }
      }
    }
  }
  ${METADATA_ENTRY_FRAGMENT}
  ${DAGSTER_TYPE_FRAGMENT}
`;
