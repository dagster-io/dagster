import {gql} from '@apollo/client';
import {
  Body2,
  Box,
  Button,
  Colors,
  CursorHistoryControls,
  Dialog,
  DialogBody,
  DialogFooter,
  Mono,
  NonIdealState,
  Spinner,
  Table,
} from '@dagster-io/ui-components';
import React from 'react';
import {Link} from 'react-router-dom';

import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {useTrackPageView} from '../../app/analytics';
import {AssetKeyInput} from '../../graphql/types';
import {useDocumentTitle} from '../../hooks/useDocumentTitle';
import {METADATA_ENTRY_FRAGMENT, MetadataEntries} from '../../metadata/MetadataEntry';
import {MetadataEntryFragment} from '../../metadata/types/MetadataEntry.types';
import {linkToRunEvent} from '../../runs/RunUtils';
import {useCursorPaginatedQuery} from '../../runs/useCursorPaginatedQuery';
import {TimestampDisplay} from '../../schedules/TimestampDisplay';

import {AssetCheckStatusTag} from './AssetCheckStatusTag';
import {
  AssetCheckDetailsQuery,
  AssetCheckDetailsQueryVariables,
} from './types/AssetCheckDetailModal.types';

export const AssetCheckDetailModal = ({
  assetKey,
  checkName,
  onClose,
}: {
  assetKey: AssetKeyInput;
  checkName: string | undefined | null;
  onClose: () => void;
}) => {
  return (
    <Dialog
      isOpen={!!checkName}
      canOutsideClickClose
      canEscapeKeyClose
      onClose={onClose}
      icon="asset_check"
      title={`${checkName} run history`}
      style={{width: '80%', minWidth: '800px'}}
    >
      {checkName ? <AssetCheckDetailModalImpl checkName={checkName} assetKey={assetKey} /> : null}
    </Dialog>
  );
};

const PAGE_SIZE = 5;

const AssetCheckDetailModalImpl = ({
  assetKey,
  checkName,
}: {
  assetKey: AssetKeyInput;
  checkName: string;
}) => {
  useTrackPageView();
  useDocumentTitle(`Asset Check | ${checkName}`);

  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    AssetCheckDetailsQuery,
    AssetCheckDetailsQueryVariables
  >({
    query: ASSET_CHECK_DETAILS_QUERY,
    variables: {
      assetKey,
      checkName,
    },
    nextCursorForResult: (data) => {
      if (!data) {
        return undefined;
      }
      return data.assetCheckExecutions[PAGE_SIZE - 1]?.id.toString();
    },
    getResultArray: (data) => {
      if (!data) {
        return [];
      }
      return data.assetCheckExecutions || [];
    },
    pageSize: PAGE_SIZE,
  });

  // TODO - in a follow up PR we should have some kind of queryRefresh context that can merge all of the uses of queryRefresh.
  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  const executions = queryResult.data?.assetCheckExecutions;

  const runHistory = () => {
    if (!executions) {
      return (
        <Box padding={48}>
          <Spinner purpose="section" />
        </Box>
      );
    }

    if (!executions.length) {
      return <NoExecutions />;
    }
    return (
      <div>
        <Table>
          <thead>
            <tr>
              <th style={{width: '200px'}}>Timestamp</th>
              <th style={{width: '200px'}}>Target materialization</th>
              <th style={{width: '160px'}}>Result</th>
              <th>Evaluation metadata</th>
            </tr>
          </thead>
          <tbody>
            {executions.map((execution) => {
              return (
                <tr key={execution.id}>
                  <td>
                    {execution.evaluation?.timestamp ? (
                      <Link
                        to={linkToRunEvent(
                          {id: execution.runId},
                          {stepKey: execution.stepKey, timestamp: execution.timestamp},
                        )}
                      >
                        <TimestampDisplay timestamp={execution.evaluation.timestamp} />
                      </Link>
                    ) : (
                      <TimestampDisplay timestamp={execution.timestamp} />
                    )}
                  </td>
                  <td>
                    {execution.evaluation?.targetMaterialization ? (
                      <Link to={`/runs/${execution.evaluation.targetMaterialization.runId}`}>
                        <TimestampDisplay
                          timestamp={execution.evaluation.targetMaterialization.timestamp}
                        />
                      </Link>
                    ) : (
                      ' - '
                    )}
                  </td>
                  <td>
                    <AssetCheckStatusTag execution={execution} />
                  </td>
                  <td>
                    <MetadataCell metadataEntries={execution.evaluation?.metadataEntries} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </Table>
        <div style={{paddingBottom: '16px'}}>
          <CursorHistoryControls {...paginationProps} />
        </div>
      </div>
    );
  };

  if (!executions) {
    return (
      <Box flex={{direction: 'column'}} padding={24}>
        <Spinner purpose="section" />
      </Box>
    );
  }
  return <Box flex={{direction: 'column'}}>{runHistory()}</Box>;
};

export function MetadataCell({metadataEntries}: {metadataEntries?: MetadataEntryFragment[]}) {
  const [showMetadata, setShowMetadata] = React.useState(false);

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
            <Body2 color={Colors.Gray700} style={{padding: '6px 0'}}>
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
            <Body2 color={Colors.Gray700} style={{padding: '6px 0'}}>
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
            <Body2 color={Colors.Gray700} style={{padding: '6px 0'}}>
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
            <Body2 color={Colors.Gray700} style={{padding: '6px 0'}}>
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
              <Icon name="open_in_new" color={Colors.Link} />
            </Box> */}
          </Box>
        }
      />
    </Box>
  );
}

function NoExecutions() {
  return (
    <Box padding={24}>
      <NonIdealState
        icon="asset_check"
        title="No executions found for this check"
        description={
          <Box flex={{direction: 'column'}}>
            <Body2 color={Colors.Gray700} style={{padding: '6px 0'}}>
              No executions found. Materialize this asset and the check will run automatically.
            </Body2>
            {/* <Box
              as="a"
              href="https://docs.dagster.io/concepts/assets/asset-checks"
              target="_blank"
              flex={{direction: 'row', alignItems: 'end', gap: 4}}
            >
              Learn more about Asset Checks
              <Icon name="open_in_new" color={Colors.Link} />
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
