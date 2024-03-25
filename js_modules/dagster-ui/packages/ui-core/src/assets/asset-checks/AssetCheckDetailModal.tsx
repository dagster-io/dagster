import {gql} from '@apollo/client';
import {
  Body2,
  Box,
  Button,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Mono,
  NonIdealState,
} from '@dagster-io/ui-components';
import {useState} from 'react';

import {METADATA_ENTRY_FRAGMENT, MetadataEntries} from '../../metadata/MetadataEntry';
import {MetadataEntryFragment} from '../../metadata/types/MetadataEntry.types';

export function MetadataCell({metadataEntries}: {metadataEntries?: MetadataEntryFragment[]}) {
  const [showMetadata, setShowMetadata] = useState(false);

  if (!metadataEntries || !metadataEntries.length) {
    return <span>{' - '}</span>;
  }
  if (canShowMetadataInline(metadataEntries)) {
    return <MetadataEntries entries={metadataEntries} />;
  }
  return (
    <div>
      <Button onClick={() => setShowMetadata(true)}>View metadata</Button>
      <Dialog
        title="Metadata"
        isOpen={showMetadata}
        onClose={() => setShowMetadata(false)}
        canOutsideClickClose
        canEscapeKeyClose
        style={{width: '80%', minWidth: '800px'}}
      >
        <DialogBody>
          <MetadataEntries entries={metadataEntries} />
        </DialogBody>
        <DialogFooter topBorder>
          <Button onClick={() => setShowMetadata(false)} intent="primary">
            Close
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

export const ASSET_CHECK_EXECUTION_FRAGMENT = gql`
  fragment AssetCheckExecutionFragment on AssetCheckExecution {
    id
    runId
    status
    stepKey
    timestamp
    evaluation {
      severity
      timestamp
      description
      targetMaterialization {
        timestamp
        runId
      }
      metadataEntries {
        ...MetadataEntryFragment
      }
    }
  }
  ${METADATA_ENTRY_FRAGMENT}
`;

export const ASSET_CHECK_DETAILS_QUERY = gql`
  query AssetCheckDetailsQuery(
    $assetKey: AssetKeyInput!
    $checkName: String!
    $limit: Int!
    $cursor: String
  ) {
    assetCheckExecutions(
      assetKey: $assetKey
      checkName: $checkName
      limit: $limit
      cursor: $cursor
    ) {
      id
      ...AssetCheckExecutionFragment
    }
  }
  ${ASSET_CHECK_EXECUTION_FRAGMENT}
`;

export function MigrationRequired() {
  return (
    <Box padding={24}>
      <NonIdealState
        icon="warning"
        title="Migration required"
        description={
          <Box flex={{direction: 'column'}}>
            <Body2 color={Colors.textLight()} style={{padding: '6px 0'}}>
              A database schema migration is required to use asset checks. Run{' '}
              <Mono>dagster instance migrate</Mono>.
            </Body2>
          </Box>
        }
      />
    </Box>
  );
}

export function AgentUpgradeRequired() {
  return (
    <Box padding={24}>
      <NonIdealState
        icon="warning"
        title="Agent upgrade required"
        description={
          <Box flex={{direction: 'column'}}>
            <Body2 color={Colors.textLight()} style={{padding: '6px 0'}}>
              Checks require Dagster Cloud Agent version 1.5 or higher. Upgrade your agent(s) to use
              checks.
            </Body2>
          </Box>
        }
      />
    </Box>
  );
}

export function NeedsUserCodeUpgrade() {
  return (
    <Box padding={24}>
      <NonIdealState
        icon="warning"
        title="Upgrade required"
        description={
          <Box flex={{direction: 'column'}}>
            <Body2 color={Colors.textLight()} style={{padding: '6px 0'}}>
              Checks aren&apos;t supported with dagster versions before 1.5. Upgrade the dagster
              library in this code location to use them.
            </Body2>
          </Box>
        }
      />
    </Box>
  );
}

export function NoChecks() {
  return (
    <Box padding={24}>
      <NonIdealState
        icon="asset_check"
        title="No checks found for this asset"
        description={
          <Box flex={{direction: 'column'}}>
            <Body2 color={Colors.textLight()} style={{padding: '6px 0'}}>
              Asset Checks run after a materialization and can verify a particular property of a
              data asset. Checks can help ensure that the contents of each data asset is correct.
            </Body2>
            {/* <Box
              as="a"
              href="https://docs.dagster.io/concepts/assets/asset-checks"
              target="_blank"
              flex={{direction: 'row', alignItems: 'end', gap: 4}}
            >
              Learn more about Asset Checks
              <Icon name="open_in_new" color={Colors.linkDefault()} />
            </Box> */}
          </Box>
        }
      />
    </Box>
  );
}

const InlineableTypenames: MetadataEntryFragment['__typename'][] = [
  'BoolMetadataEntry',
  'FloatMetadataEntry',
  'IntMetadataEntry',
  'TextMetadataEntry',
  'UrlMetadataEntry',
  'PathMetadataEntry',
  'NullMetadataEntry',
  'TableSchemaMetadataEntry',
];
function canShowMetadataInline(entries: MetadataEntryFragment[]) {
  if (entries.length > 1) {
    return false;
  }
  if (InlineableTypenames.includes(entries[0]?.__typename as any)) {
    return true;
  }
  if (entries[0]?.__typename === 'TableMetadataEntry' && entries[0].table.records.length <= 1) {
    return true;
  }
  return false;
}
