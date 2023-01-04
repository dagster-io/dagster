import {Box, MetadataTable} from '@dagster-io/ui';
import * as React from 'react';

import {graphql} from '../graphql';
import {
  AssetNodeOpMetadataFragmentFragment,
  DagsterTypeFragmentFragment,
  MetadataEntryFragmentFragment,
} from '../graphql/graphql';
import {MetadataEntry} from '../metadata/MetadataEntry';

export const metadataForAssetNode = (
  assetNode: AssetNodeOpMetadataFragmentFragment,
): {assetType?: DagsterTypeFragmentFragment; assetMetadata: MetadataEntryFragmentFragment[]} => {
  const assetType = assetNode.type ? assetNode.type : undefined;
  const assetMetadata = assetNode.metadataEntries || [];
  return {assetType, assetMetadata};
};

export const AssetMetadataTable: React.FC<{
  assetMetadata: MetadataEntryFragmentFragment[];
  repoLocation: string;
}> = ({assetMetadata, repoLocation}) => {
  const rows = assetMetadata.map((entry) => {
    return {
      key: entry.label,
      value: <MetadataEntry entry={entry} repoLocation={repoLocation} />,
    };
  });
  return (
    <Box padding={{vertical: 16, horizontal: 24}}>
      <MetadataTable rows={rows} />
    </Box>
  );
};

export const ASSET_NODE_OP_METADATA_FRAGMENT = graphql(`
  fragment AssetNodeOpMetadataFragment on AssetNode {
    id
    metadataEntries {
      ...MetadataEntryFragment
    }
    type {
      ...DagsterTypeFragment
    }
  }
`);
