import {gql, useQuery} from '@apollo/client';
import {
  Body2,
  Box,
  Caption,
  CollapsibleSection,
  Colors,
  Icon,
  NonIdealState,
  Subtitle1,
  Subtitle2,
  TextInput,
  useViewport,
} from '@dagster-io/ui-components';
import {RowProps} from '@dagster-io/ui-components/src/components/VirtualizedTable';
import {useVirtualizer} from '@tanstack/react-virtual';
import React, {useContext} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {AssetCheckStatusTag} from './AssetCheckStatusTag';
import {
  EXECUTE_CHECKS_BUTTON_ASSET_NODE_FRAGMENT,
  EXECUTE_CHECKS_BUTTON_CHECK_FRAGMENT,
  ExecuteChecksButton,
} from './ExecuteChecksButton';
import {ASSET_CHECK_TABLE_FRAGMENT} from './VirtualizedAssetCheckTable';
import {AssetChecksQuery, AssetChecksQueryVariables} from './types/AssetChecks.types';
import {ExecuteChecksButtonCheckFragment} from './types/ExecuteChecksButton.types';
import {assetCheckStatusDescription, getCheckIcon} from './util';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {COMMON_COLLATOR} from '../../app/Util';
import {Timestamp} from '../../app/time/Timestamp';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {useStateWithStorage} from '../../hooks/useStateWithStorage';
import {linkToRunEvent} from '../../runs/RunUtils';
import {Container, Inner, Row} from '../../ui/VirtualizedTable';
import {numberFormatter} from '../../ui/formatters';
import {AssetFeatureContext} from '../AssetFeatureContext';
import {AssetKey} from '../types';

export const AssetChecks = ({
  lastMaterializationTimestamp,
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

  function executeButton(check?: ExecuteChecksButtonCheckFragment) {
    const assetNode = data?.assetNodeOrError;
    if (assetNode?.__typename !== 'AssetNode') {
      return <span />;
    }
    const checksOrError = assetNode.assetChecksOrError;
    if (checksOrError?.__typename !== 'AssetChecks') {
      return <span />;
    }
    return (
      <ExecuteChecksButton
        assetNode={assetNode}
        checks={check ? [check] : checksOrError.checks}
        label={check ? 'Execute' : undefined}
      />
    );
  }

  const {AssetChecksBanner} = useContext(AssetFeatureContext);

  const [didDismissAssetChecksBanner, setDidDismissAssetChecksBanner] = useStateWithStorage(
    'asset-checks-experimental-banner',
    (json) => !!json,
  );

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

  React.useEffect(() => {}, []);

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

  if (!checks.length || !selectedCheck) {
    return (
      <Box flex={{alignItems: 'center'}} padding={32}>
        <NonIdealState
          title="No checks defined for this asset"
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
            {executeButton()}
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
            {executeButton(selectedCheck)}
          </Box>
          <Box
            flex={{grow: 1, direction: 'column', gap: 12}}
            padding={{horizontal: 24, vertical: 12}}
          >
            <CollapsibleSection
              header={<Subtitle2>About</Subtitle2>}
              headerWrapperProps={headerWrapperProps}
            >
              <Box border="bottom" padding={{vertical: 12}}>
                <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 24}}>
                  <Box flex={{direction: 'column', gap: 5}}>
                    <Subtitle2>Evaluation Result</Subtitle2>
                    <div>
                      <AssetCheckStatusTag
                        execution={selectedCheck.executionForLatestMaterialization}
                      />
                    </div>
                  </Box>
                  {lastExecution ? (
                    <Box flex={{direction: 'column', gap: 5}}>
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
                    <Box flex={{direction: 'column', gap: 5}}>
                      <Subtitle2>Target materialization</Subtitle2>
                      <Link to={`/runs/${targetMaterialization.runId}`}>
                        <Timestamp timestamp={{unix: targetMaterialization.timestamp}} />
                      </Link>
                    </Box>
                  ) : null}
                </div>
              </Box>
            </CollapsibleSection>
            <CollapsibleSection
              header={<Subtitle2>Latest execution</Subtitle2>}
              headerWrapperProps={headerWrapperProps}
            >
              <Box padding={{vertical: 12}}>
                <Subtitle2>About</Subtitle2>
              </Box>
            </CollapsibleSection>
            <CollapsibleSection
              header={<Subtitle2>Execution history</Subtitle2>}
              headerWrapperProps={headerWrapperProps}
            >
              <Box padding={{vertical: 12}}>
                <Subtitle2>About</Subtitle2>
              </Box>
            </CollapsibleSection>
          </Box>
        </Box>
      </Box>
    </Box>
  );
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
    background: ${Colors.backgroundBlue()};
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
              ...AssetCheckTableFragment
              ...ExecuteChecksButtonCheckFragment
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
