import {gql} from '@apollo/client';
import {Box, MetadataTable} from '@dagster-io/ui-components';

import {AssetNodeOpMetadataFragment} from './types/AssetMetadata.types';
import {DAGSTER_TYPE_FRAGMENT} from '../dagstertype/DagsterType';
import {DagsterTypeFragment} from '../dagstertype/types/DagsterType.types';
import {
  HIDDEN_METADATA_ENTRY_LABELS,
  METADATA_ENTRY_FRAGMENT,
  MetadataEntry,
} from '../metadata/MetadataEntry';
import {MetadataEntryFragment} from '../metadata/types/MetadataEntry.types';

export const metadataForAssetNode = (
  assetNode: AssetNodeOpMetadataFragment,
): {assetType?: DagsterTypeFragment; assetMetadata: MetadataEntryFragment[]} => {
  const assetType = assetNode.type ? assetNode.type : undefined;
  const assetMetadata = assetNode.metadataEntries || [];
  return {assetType, assetMetadata};
};

export const AssetMetadataTable = ({
  assetMetadata,
  repoLocation,
}: {
  assetMetadata: MetadataEntryFragment[];
  repoLocation: string;
}) => {
  const rows = assetMetadata
    .filter((entry) => !HIDDEN_METADATA_ENTRY_LABELS.has(entry.label))
    .map((entry) => {
      return {
        key: entry.label,
        value: <MetadataEntry entry={entry} repoLocation={repoLocation} />,
      };
    });
  return (
    <Box padding={{vertical: 16, horizontal: 24}} style={{overflowX: 'auto'}}>
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
