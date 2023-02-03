import {gql} from '@apollo/client';
import {Box, MetadataTable} from '@dagster-io/ui';
import * as React from 'react';

import {DAGSTER_TYPE_FRAGMENT} from '../dagstertype/DagsterType';
import {DagsterTypeFragment} from '../dagstertype/types/DagsterType.types';
import {MetadataEntry, METADATA_ENTRY_FRAGMENT} from '../metadata/MetadataEntry';
import {MetadataEntryFragment} from '../metadata/types/MetadataEntry.types';

import {AssetNodeOpMetadataFragment} from './types/AssetMetadata.types';

export const metadataForAssetNode = (
  assetNode: AssetNodeOpMetadataFragment,
): {assetType?: DagsterTypeFragment; assetMetadata: MetadataEntryFragment[]} => {
  const assetType = assetNode.type ? assetNode.type : undefined;
  const assetMetadata = (assetNode.metadataEntries || []).filter(
    (entry) => entry.label !== '__code_origin',
  );
  return {assetType, assetMetadata};
};

export const AssetMetadataTable: React.FC<{
  assetMetadata: MetadataEntryFragment[];
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

export const ASSET_NODE_OP_METADATA_FRAGMENT = gql`
  fragment AssetNodeOpMetadataFragment on AssetNode {
    id
    metadataEntries {
      ...MetadataEntryFragment
    }
    type {
      ...DagsterTypeFragment
    }
  }

  ${METADATA_ENTRY_FRAGMENT}
  ${DAGSTER_TYPE_FRAGMENT}
`;
