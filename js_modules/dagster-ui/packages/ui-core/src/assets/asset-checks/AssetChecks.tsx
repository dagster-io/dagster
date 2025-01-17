import {
  Body2,
  Box,
  Caption,
  Colors,
  Icon,
  MiddleTruncate,
  NonIdealState,
  Subtitle1,
  TextInput,
  useViewport,
} from '@dagster-io/ui-components';
import {RowProps} from '@dagster-io/ui-components/src/components/VirtualizedTable';
import {useVirtualizer} from '@tanstack/react-virtual';
import React, {useMemo, useState} from 'react';
import styled from 'styled-components';

import {AssetCheckAutomationList} from './AssetCheckAutomationList';
import {
  ASSET_CHECK_DETAILS_QUERY,
  AgentUpgradeRequired,
  MigrationRequired,
  NeedsUserCodeUpgrade,
} from './AssetCheckDetailDialog';
import {AssetCheckExecutionList} from './AssetCheckExecutionList';
import {AssetCheckOverview} from './AssetCheckOverview';
import {ASSET_CHECKS_QUERY} from './AssetChecksQuery';
import {ExecuteChecksButton} from './ExecuteChecksButton';
import {
  AssetCheckDetailsQuery,
  AssetCheckDetailsQueryVariables,
} from './types/AssetCheckDetailDialog.types';
import {assetCheckStatusDescription, getCheckIcon} from './util';
import {useQuery} from '../../apollo-client';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {COMMON_COLLATOR, assertUnreachable} from '../../app/Util';
import {AssetKeyInput} from '../../graphql/types';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {useCursorPaginatedQuery} from '../../runs/useCursorPaginatedQuery';
import {Container, Inner, Row} from '../../ui/VirtualizedTable';
import {numberFormatter} from '../../ui/formatters';
import {PAGE_SIZE} from '../AutoMaterializePolicyPage/useEvaluationsQueryResult';
import {AssetKey} from '../types';
import {AssetChecksTabType, AssetChecksTabs} from './AssetChecksTabs';
import {AssetChecksQuery, AssetChecksQueryVariables} from './types/AssetChecksQuery.types';

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

  const [activeTab, setActiveTab] = useState<AssetChecksTabType>('overview');

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

  const isSelectedCheckAutomated = !!selectedCheck?.automationCondition;

  const {paginationProps, executions, executionsLoading} = useHistoricalCheckExecutions(
    selectedCheck ? {assetKey, checkName: selectedCheck.name} : null,
  );
  const pastExecutions = useMemo(() => executions.slice(1), [executions]);

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
            <Box flex={{direction: 'column', gap: 8}}>
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
  const targetMaterialization = lastExecution?.evaluation?.targetMaterialization ?? null;

  return (
    <Box flex={{grow: 1, direction: 'column'}}>
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
                          setActiveTab('overview');
                        }}
                      >
                        <Box flex={{direction: 'column', gap: 2}}>
                          <Box flex={{direction: 'row', gap: 8, alignItems: 'flex-start'}}>
                            <Box
                              flex={{alignItems: 'center', justifyContent: 'center'}}
                              style={{
                                width: 20,
                                height: 20,
                              }}
                            >
                              {getCheckIcon(check)}
                            </Box>
                            <Body2 style={{overflow: 'hidden'}}>
                              <MiddleTruncate text={check.name} />
                              <Caption
                                color={Colors.textLight()}
                                style={{textTransform: 'capitalize'}}
                              >
                                {assetCheckStatusDescription(check)}
                              </Caption>
                            </Body2>
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
            <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
              <Icon name="asset_check" />
              <Subtitle1>{selectedCheck.name}</Subtitle1>
            </Box>
            <ExecuteChecksButton assetNode={assetNode} checks={[selectedCheck]} label="Execute" />
          </Box>
          <Box padding={{horizontal: 24}} border="bottom">
            <AssetChecksTabs
              activeTab={activeTab}
              enableAutomationHistory={isSelectedCheckAutomated}
              onChange={(tab) => {
                setActiveTab(tab);
              }}
            />
          </Box>
          {activeTab === 'overview' ? (
            <AssetCheckOverview
              selectedCheck={selectedCheck}
              lastExecution={lastExecution}
              targetMaterialization={targetMaterialization}
              executions={executions}
              executionsLoading={executionsLoading}
            />
          ) : null}
          {activeTab === 'execution-history' ? (
            <AssetCheckExecutionList
              executions={pastExecutions}
              paginationProps={paginationProps}
            />
          ) : null}
          {activeTab === 'automation-history' ? (
            <AssetCheckAutomationList assetCheck={selectedCheck} checkName={selectedCheck.name} />
          ) : null}
        </Box>
      </Box>
    </Box>
  );
};

const useHistoricalCheckExecutions = (
  variables: {assetKey: AssetKeyInput; checkName: string} | null,
) => {
  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    AssetCheckDetailsQuery,
    AssetCheckDetailsQueryVariables
  >({
    query: ASSET_CHECK_DETAILS_QUERY,
    skip: !variables,
    variables: variables || {assetKey: {path: []}, checkName: ''},
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

  const executionsLoading = queryResult.loading && !queryResult.data;
  const executions = React.useMemo(
    // Remove first element since the latest execution info is already shown above
    () => queryResult.data?.assetCheckExecutions || [],
    [queryResult],
  );
  return {executions, executionsLoading, paginationProps};
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
