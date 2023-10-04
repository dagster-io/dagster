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
  DialogHeader,
  Headline,
  Mono,
  NonIdealState,
  Spinner,
  Subtitle2,
  Table,
} from '@dagster-io/ui-components';
import React from 'react';
import {Link} from 'react-router-dom';

import {showCustomAlert} from '../../app/CustomAlertProvider';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {useTrackPageView} from '../../app/analytics';
import {AssetKeyInput} from '../../graphql/types';
import {useDocumentTitle} from '../../hooks/useDocumentTitle';
import {METADATA_ENTRY_FRAGMENT, MetadataEntries} from '../../metadata/MetadataEntry';
import {MetadataEntryFragment} from '../../metadata/types/MetadataEntry.types';
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
      style={{width: '80%', minWidth: '800px'}}
    >
      {checkName ? (
        <AssetCheckDetailModalImpl checkName={checkName} assetKey={assetKey} onClose={onClose} />
      ) : null}
    </Dialog>
  );
};

const PAGE_SIZE = 5;
const AssetCheckDetailModalImpl = ({
  assetKey,
  checkName,
  onClose,
}: {
  assetKey: AssetKeyInput;
  checkName: string;
  onClose: () => void;
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
      if (
        !data ||
        data.assetChecksOrError.__typename === 'AssetCheckNeedsMigrationError' ||
        data.assetChecksOrError.__typename === 'AssetCheckNeedsUserCodeUpgrade'
      ) {
        return undefined;
      }
      return data.assetChecksOrError.checks[0]?.executions[PAGE_SIZE - 1]?.id.toString();
    },
    getResultArray: (data) => {
      if (
        !data ||
        data.assetChecksOrError.__typename === 'AssetCheckNeedsMigrationError' ||
        data.assetChecksOrError.__typename === 'AssetCheckNeedsUserCodeUpgrade'
      ) {
        return [];
      }
      return data.assetChecksOrError.checks[0]?.executions || [];
    },
    pageSize: PAGE_SIZE,
  });

  // TODO - in a follow up PR we should have some kind of queryRefresh context that can merge all of the uses of queryRefresh.
  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  const {data: executionHistoryData} = queryResult;

  const content = () => {
    if (!executionHistoryData) {
      return (
        <Box flex={{direction: 'column'}} padding={24}>
          <Spinner purpose="page" />
        </Box>
      );
    }
    return (
      <Box
        flex={{direction: 'column'}}
        border="top"
        // CollapsibleSection uses a white background which covers the border, so add 1px of padding on top for the border
        padding={{top: 1, horizontal: 12}}
      >
        <Subtitle2 style={{padding: '8px 16px'}}>Run history</Subtitle2>
        {runHistory()}
      </Box>
    );
  };

  const runHistory = () => {
    if (!executionHistoryData) {
      return (
        <Box padding={48}>
          <Spinner purpose="page" />
        </Box>
      );
    }
    if (executionHistoryData.assetChecksOrError.__typename === 'AssetCheckNeedsMigrationError') {
      return <MigrationRequired />;
    }
    if (executionHistoryData.assetChecksOrError.__typename === 'AssetCheckNeedsUserCodeUpgrade') {
      return <MigrationRequired />;
    }
    const check = executionHistoryData.assetChecksOrError.checks[0];
    if (!check) {
      showCustomAlert({
        title: 'Error',
        body: `Asset Check ${checkName} not found`,
      });
      setTimeout(() => {
        // This check does not exist
        onClose();
      });
      return <NoChecks />;
    }
    const executions = check.executions;
    if (!executions.length) {
      return <NoExecutions />;
    }
    return (
      <div>
        <Table>
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Target materialization</th>
              <th>Result</th>
              <th>Evaluation metadata</th>
            </tr>
          </thead>
          <tbody>
            {executions.map((execution) => {
              return (
                <tr key={execution.id}>
                  <td>
                    {execution.evaluation?.timestamp ? (
                      <Link to={`/runs/${execution.runId}`}>
                        <TimestampDisplay timestamp={execution.evaluation.timestamp} />
                      </Link>
                    ) : (
                      ' - '
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
                    <AssetCheckStatusTag check={check} execution={execution} />
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

  return (
    <>
      <DialogHeader label={<Headline>{checkName}</Headline>} icon="asset_check"></DialogHeader>
      {content()}
    </>
  );
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
    assetChecksOrError(assetKey: $assetKey, checkName: $checkName) {
      ... on AssetChecks {
        checks {
          name
          description
          executions(limit: $limit, cursor: $cursor) {
            ...AssetCheckExecutionFragment
          }
        }
      }
      ... on AssetCheckNeedsMigrationError {
        message
      }
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
