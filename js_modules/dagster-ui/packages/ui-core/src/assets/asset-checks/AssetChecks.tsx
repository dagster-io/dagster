import {gql, useQuery} from '@apollo/client';
import {
  Body2,
  Box,
  Caption,
  CollapsibleSection,
  Colors,
  CursorHistoryControls,
  Icon,
  NonIdealState,
  Spinner,
  Subtitle1,
  Subtitle2,
  Table,
  TextInput,
  useViewport,
} from '@dagster-io/ui-components';
import {RowProps} from '@dagster-io/ui-components/src/components/VirtualizedTable';
import {useVirtualizer} from '@tanstack/react-virtual';
import React, {useContext} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {
  ASSET_CHECK_DETAILS_QUERY,
  AgentUpgradeRequired,
  MetadataCell,
  MigrationRequired,
  NeedsUserCodeUpgrade,
} from './AssetCheckDetailModal';
import {AssetCheckStatusTag} from './AssetCheckStatusTag';
import {
  EXECUTE_CHECKS_BUTTON_ASSET_NODE_FRAGMENT,
  EXECUTE_CHECKS_BUTTON_CHECK_FRAGMENT,
  ExecuteChecksButton,
} from './ExecuteChecksButton';
import {ASSET_CHECK_TABLE_FRAGMENT} from './VirtualizedAssetCheckTable';
import {
  AssetCheckDetailsQuery,
  AssetCheckDetailsQueryVariables,
} from './types/AssetCheckDetailModal.types';
import {AssetChecksQuery, AssetChecksQueryVariables} from './types/AssetChecks.types';
import {assetCheckStatusDescription, getCheckIcon} from './util';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {COMMON_COLLATOR, assertUnreachable} from '../../app/Util';
import {Timestamp} from '../../app/time/Timestamp';
import {AssetKeyInput} from '../../graphql/types';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {useStateWithStorage} from '../../hooks/useStateWithStorage';
import {MetadataEntries} from '../../metadata/MetadataEntry';
import {linkToRunEvent} from '../../runs/RunUtils';
import {useCursorPaginatedQuery} from '../../runs/useCursorPaginatedQuery';
import {TimestampDisplay} from '../../schedules/TimestampDisplay';
import {Container, Inner, Row} from '../../ui/VirtualizedTable';
import {numberFormatter} from '../../ui/formatters';
import {AssetFeatureContext} from '../AssetFeatureContext';
import {PAGE_SIZE} from '../AutoMaterializePolicyPage/useEvaluationsQueryResult';
import {AssetKey} from '../types';

export const AssetChecks = ({
  assetKey,
}: {
  assetKey: AssetKey;
  lastMaterializationTimestamp: string | undefined;
}) => {
  const queryResult = useQuery<AssetChecksQuery, AssetChecksQueryVariables>(ASSET_CHECKS_QUERY, {
    variables: {assetKey},
  });
  const {data} = queryResult;
  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  const [selectedCheckName, setSelectedCheckName] = useQueryPersistedState<string>({
    queryKey: 'checkDetail',
  });

  const assetNode =
    data?.assetNodeOrError.__typename === 'AssetNode' ? data.assetNodeOrError : null;

  const checks = React.useMemo(() => {
    if (data?.assetNodeOrError.__typename !== 'AssetNode') {
      return [];
    }
    if (data.assetNodeOrError.assetChecksOrError.__typename !== 'AssetChecks') {
      return [];
    }
    return [...data.assetNodeOrError.assetChecksOrError.checks].sort((a, b) =>
      COMMON_COLLATOR.compare(a.name, b.name),
    );
  }, [data]);

  const {AssetChecksBanner} = useContext(AssetFeatureContext);

  const [didDismissAssetChecksBanner, setDidDismissAssetChecksBanner] = useStateWithStorage(
    'asset-checks-experimental-banner',
    (json) => !!json,
  );

  const [searchValue, setSearchValue] = React.useState('');

  const filteredChecks = React.useMemo(() => {
    return checks.filter((check) => check.name.toLowerCase().includes(searchValue.toLowerCase()));
  }, [checks, searchValue]);

  const containerRef = React.useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: filteredChecks.length,
    getScrollElement: () => containerRef.current,
    estimateSize: () => 48,
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  const selectedCheck = React.useMemo(() => {
    if (!selectedCheckName) {
      return checks[0];
    }
    return checks.find((check) => check.name === selectedCheckName) ?? checks[0];
  }, [selectedCheckName, checks]);

  if (!data) {
    return null;
  }

  if (data.assetNodeOrError.__typename === 'AssetNode') {
    const type = data.assetNodeOrError.assetChecksOrError.__typename;
    switch (type) {
      case 'AssetCheckNeedsAgentUpgradeError':
        return <AgentUpgradeRequired />;
      case 'AssetCheckNeedsMigrationError':
        return <MigrationRequired />;
      case 'AssetCheckNeedsUserCodeUpgrade':
        return <NeedsUserCodeUpgrade />;
      case 'AssetChecks':
        break;
      default:
        assertUnreachable(type);
    }
  }

  if (!checks.length || !selectedCheck || !assetNode) {
    return (
      <Box flex={{alignItems: 'center'}} padding={32}>
        <NonIdealState
          title="No checks defined for this asset"
          icon="asset_check"
          description={
            <Box flex={{direction: 'column', gap: 6}}>
              <Body2>
                Asset checks can verify properties of a data asset, e.g. that there are no null
                values in a particular column.
              </Body2>
              <a href="https://docs.dagster.io/concepts/assets/asset-checks">
                Learn more about asset checks
              </a>
            </Box>
          }
        />
      </Box>
    );
  }

  const lastExecution = selectedCheck.executionForLatestMaterialization;
  const targetMaterialization = lastExecution?.evaluation?.targetMaterialization;

  console.log({lastExecution});

  return (
    <Box flex={{grow: 1, direction: 'column'}}>
      {didDismissAssetChecksBanner ? null : (
        <Box padding={{horizontal: 24, vertical: 12}} border="bottom">
          <AssetChecksBanner
            onClose={() => {
              setDidDismissAssetChecksBanner(true);
            }}
          />
        </Box>
      )}
      <Box flex={{direction: 'row', grow: 1}} style={{position: 'relative'}}>
        <Box flex={{direction: 'column'}} style={{minWidth: 294, width: '20%'}} border="right">
          <Box
            style={{height: 56}}
            border="bottom"
            flex={{justifyContent: 'space-between', alignItems: 'center'}}
            padding={{left: 24, vertical: 12, right: 12}}
          >
            <Subtitle1>
              Checks {checks.length ? <>({numberFormatter.format(checks.length)})</> : null}
            </Subtitle1>
            <ExecuteChecksButton assetNode={assetNode} checks={checks} />
          </Box>
          <Box
            flex={{direction: 'column', gap: 8, grow: 1}}
            padding={{horizontal: 16, vertical: 12}}
          >
            <TextInput
              icon="search"
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              placeholder="Filter checks"
            />
            <FixedScrollContainer>
              <Container ref={containerRef}>
                <Inner $totalHeight={totalHeight}>
                  {items.map(({index, size, start}) => {
                    const check = filteredChecks[index]!;
                    return (
                      <CheckRow
                        key={check.name}
                        $height={size}
                        $start={start}
                        $selected={selectedCheck === check}
                        onClick={() => {
                          setSelectedCheckName(check.name);
                        }}
                      >
                        <Box flex={{direction: 'column', gap: 2}}>
                          <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                            <Box
                              flex={{alignItems: 'center', justifyContent: 'center'}}
                              style={{
                                width: 20,
                                height: 20,
                              }}
                            >
                              {getCheckIcon(check)}
                            </Box>
                            <Body2>{check.name}</Body2>
                          </Box>
                          <Box padding={{horizontal: 24}}>
                            <Caption
                              color={Colors.textLight()}
                              style={{textTransform: 'capitalize'}}
                            >
                              {assetCheckStatusDescription(check)}
                            </Caption>
                          </Box>
                        </Box>
                      </CheckRow>
                    );
                  })}
                </Inner>
              </Container>
            </FixedScrollContainer>
          </Box>
        </Box>
        <Box flex={{direction: 'column'}} style={{flex: 1}}>
          <Box
            style={{height: 56}}
            border="bottom"
            flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
            padding={{vertical: 12, horizontal: 24}}
          >
            <Box flex={{direction: 'row', gap: 6, alignItems: 'center'}}>
              <Icon name="asset_check" />
              <Subtitle1>{selectedCheck.name}</Subtitle1>
            </Box>
            <ExecuteChecksButton assetNode={assetNode} checks={[selectedCheck]} label="Execute" />
          </Box>
          <Box
            flex={{grow: 1, direction: 'column', gap: 12}}
            padding={{horizontal: 24, vertical: 12}}
          >
            <CollapsibleSection
              header={<Subtitle2>About</Subtitle2>}
              headerWrapperProps={headerWrapperProps}
              arrowSide="right"
            >
              <Box padding={{top: 12}} flex={{gap: 12, direction: 'column'}}>
                <Body2>
                  {selectedCheck.description ?? (
                    <Caption color={Colors.textLight()}>No description provided</Caption>
                  )}
                </Body2>
                {/* {selectedCheck.dependencies?.length ? (
                  <Box flex={{direction: 'row', gap: 6}}>
                    {assetNode.dependencies.map((dep) => {
                      const key = dep.asset.assetKey;
                      return (
                        <Link to={assetDetailsPathForKey(key)} key={tokenForAssetKey(key)}>
                          <Tag icon="asset">{displayNameForAssetKey(key)}</Tag>
                        </Link>
                      );
                    })}
                  </Box>
                ) : (
                  <Caption color={Colors.textLight()}>No dependencies</Caption>
                )} */}
              </Box>
            </CollapsibleSection>
            <CollapsibleSection
              header={<Subtitle2>Latest execution</Subtitle2>}
              headerWrapperProps={headerWrapperProps}
              arrowSide="right"
            >
              {lastExecution?.evaluation?.description ? (
                <Box padding={{top: 12}} flex={{gap: 12, direction: 'column'}}>
                  <Body2>{lastExecution.evaluation.description}</Body2>
                </Box>
              ) : null}
              <Box padding={{top: 12}} flex={{direction: 'column', gap: 12}}>
                <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 24}}>
                  <Box flex={{direction: 'column', gap: 6}}>
                    <Subtitle2>Evaluation result</Subtitle2>
                    <div>
                      <AssetCheckStatusTag
                        execution={selectedCheck.executionForLatestMaterialization}
                      />
                    </div>
                  </Box>
                  {lastExecution ? (
                    <Box flex={{direction: 'column', gap: 6}}>
                      <Subtitle2>Timestamp</Subtitle2>
                      <Link
                        to={linkToRunEvent(
                          {id: lastExecution.runId},
                          {stepKey: lastExecution.stepKey, timestamp: lastExecution.timestamp},
                        )}
                      >
                        <Timestamp timestamp={{unix: lastExecution.timestamp}} />
                      </Link>
                    </Box>
                  ) : null}
                  {targetMaterialization ? (
                    <Box flex={{direction: 'column', gap: 6}}>
                      <Subtitle2>Target materialization</Subtitle2>
                      <Link to={`/runs/${targetMaterialization.runId}`}>
                        <Timestamp timestamp={{unix: targetMaterialization.timestamp}} />
                      </Link>
                    </Box>
                  ) : null}
                </div>
                {lastExecution?.evaluation?.metadataEntries.length ? (
                  <Box flex={{direction: 'column', gap: 6}}>
                    <Subtitle2>Metadata</Subtitle2>
                    <MetadataEntries entries={lastExecution.evaluation.metadataEntries} />
                  </Box>
                ) : null}
              </Box>
            </CollapsibleSection>
            <CollapsibleSection
              header={<Subtitle2>Execution history</Subtitle2>}
              headerWrapperProps={headerWrapperProps}
              arrowSide="right"
            >
              <Box padding={{top: 12}}>
                {lastExecution ? (
                  <CheckExecutions
                    assetKey={assetKey}
                    checkName={selectedCheckName || selectedCheck.name}
                  />
                ) : (
                  <Caption color={Colors.textLight()}>No execution history</Caption>
                )}
              </Box>
            </CollapsibleSection>
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

const CheckExecutions = ({assetKey, checkName}: {assetKey: AssetKeyInput; checkName: string}) => {
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

  const executions = React.useMemo(
    // Remove first element since the latest execution info is already shown above
    () => queryResult.data?.assetCheckExecutions.slice(1),
    [queryResult],
  );

  const runHistory = () => {
    if (!executions) {
      return;
    }
    return (
      <div>
        <Table>
          <thead>
            <tr>
              <th style={{width: '160px'}}>Evaluation result</th>
              <th style={{width: '200px'}}>Timestamp</th>
              <th style={{width: '200px'}}>Target materialization</th>
              <th>Metadata</th>
            </tr>
          </thead>
          <tbody>
            {executions.map((execution) => {
              return (
                <tr key={execution.id}>
                  <td>
                    <AssetCheckStatusTag execution={execution} />
                  </td>
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

const FixedScrollContainer = ({children}: {children: React.ReactNode}) => {
  // This is kind of hacky but basically the height of the parent of this element is dynamic (its parent has flex grow)
  // but we don't want it to grow with the content inside of this node, instead we want it only to grow with the content of our sibling node.
  // This will effectively give us a height of 0
  const {viewport, containerProps} = useViewport();
  return (
    <Box flex={{grow: 1}} {...containerProps} style={{position: 'relative'}}>
      <div style={{position: 'absolute', height: viewport.height, left: 0, right: 0}}>
        {children}
      </div>
    </Box>
  );
};

const CheckRow = styled(Row)<{$selected: boolean} & RowProps>`
  padding: 5px 8px 5px 12px;
  cursor: pointer;
  border-radius: 8px;
  &:hover {
    background: ${Colors.backgroundLightHover()};
  }
  ${({$selected}) => ($selected ? `background: ${Colors.backgroundBlue()};` : '')}
`;

const headerWrapperProps: React.ComponentProps<typeof Box> = {
  border: 'bottom',
  padding: {vertical: 12},
  style: {
    cursor: 'pointer',
  },
};

export const ASSET_CHECKS_QUERY = gql`
  query AssetChecksQuery($assetKey: AssetKeyInput!) {
    assetNodeOrError(assetKey: $assetKey) {
      ... on AssetNode {
        id
        ...ExecuteChecksButtonAssetNodeFragment

        assetChecksOrError {
          ... on AssetCheckNeedsMigrationError {
            message
          }
          ... on AssetChecks {
            checks {
              ...ExecuteChecksButtonCheckFragment
              ...AssetCheckTableFragment
            }
          }
        }
      }
    }
  }
  ${EXECUTE_CHECKS_BUTTON_ASSET_NODE_FRAGMENT}
  ${EXECUTE_CHECKS_BUTTON_CHECK_FRAGMENT}
  ${ASSET_CHECK_TABLE_FRAGMENT}
`;
