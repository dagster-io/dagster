import {Box, Icon, useDelayedState} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {useRef} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {useFeatureFlags} from '../app/Flags';
import {gql, useQuery} from '../apollo-client';
import {
  SingleConcurrencyKeyQuery,
  SingleConcurrencyKeyQueryVariables,
} from './types/VirtualizedInstanceConcurrencyTable.types';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {Container, HeaderCell, HeaderRow, Inner, Row, RowCell} from '../ui/VirtualizedTable';
import {LoadingOrNone} from '../workspace/VirtualizedWorkspaceTable';

const TEMPLATE_COLUMNS = '1fr 150px 150px 150px 150px 150px';

export const ConcurrencyTable = ({concurrencyKeys}: {concurrencyKeys: string[]}) => {
  const parentRef = useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: concurrencyKeys.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 64,
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <div style={{overflow: 'hidden'}}>
      <Container ref={parentRef}>
        <ConcurrencyHeader />
        <Inner $totalHeight={totalHeight}>
          {items.map(({index, key, size, start}) => {
            const concurrencyKey = concurrencyKeys[index]!;
            return (
              <ConcurrencyRow
                key={key}
                concurrencyKey={concurrencyKey}
                height={size}
                start={start}
              />
            );
          })}
        </Inner>
      </Container>
    </div>
  );
};

const ConcurrencyHeader = () => {
  const {flagPoolUI} = useFeatureFlags();
  return (
    <HeaderRow templateColumns={TEMPLATE_COLUMNS} sticky>
      <HeaderCell>{flagPoolUI ? 'Pool' : 'Concurrency key'}</HeaderCell>
      <HeaderCell>Total slots</HeaderCell>
      <HeaderCell>Assigned steps</HeaderCell>
      <HeaderCell>Pending steps</HeaderCell>
      <HeaderCell>All steps</HeaderCell>
    </HeaderRow>
  );
};
const ConcurrencyRow = ({
  concurrencyKey,
  height,
  start,
}: {
  concurrencyKey: string;
  height: number;
  start: number;
}) => {
  // Wait 100ms before querying in case we're scrolling the table really fast
  const shouldQuery = useDelayedState(100);
  const queryResult = useQuery<SingleConcurrencyKeyQuery, SingleConcurrencyKeyQueryVariables>(
    SINGLE_CONCURRENCY_KEY_QUERY,
    {
      variables: {concurrencyKey},
      skip: !shouldQuery,
    },
  );

  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  const {data} = queryResult;
  const limit = data?.instance.concurrencyLimit;

  const path = `/deployment/concurrency/${encodeURIComponent(concurrencyKey)}`;
  return (
    <Row $height={height} $start={start}>
      <RowGrid border="bottom">
        <RowCell>
          <Box flex={{gap: 4, alignItems: 'center'}}>
            <Icon name="dynamic_feed" />
            <Link to={path}>{concurrencyKey}</Link>
          </Box>
        </RowCell>
        <RowCell>
          {limit ? <div>{limit.slotCount}</div> : <LoadingOrNone queryResult={queryResult} />}
        </RowCell>
        <RowCell>
          {limit ? (
            <>{limit.pendingSteps.filter((x) => !!x.assignedTimestamp).length}</>
          ) : (
            <LoadingOrNone queryResult={queryResult} />
          )}
        </RowCell>
        <RowCell>
          {limit ? (
            <>{limit.pendingSteps.filter((x) => !x.assignedTimestamp).length}</>
          ) : (
            <LoadingOrNone queryResult={queryResult} />
          )}
        </RowCell>
        <RowCell>
          {limit ? (
            <Box flex={{direction: 'row', gap: 16, alignItems: 'center'}}>
              <span>{limit.pendingSteps.length}</span>
            </Box>
          ) : (
            <LoadingOrNone queryResult={queryResult} />
          )}
        </RowCell>
      </RowGrid>
    </Row>
  );
};

const SINGLE_CONCURRENCY_KEY_QUERY = gql`
  query SingleConcurrencyKeyQuery($concurrencyKey: String!) {
    instance {
      id
      concurrencyLimit(concurrencyKey: $concurrencyKey) {
        concurrencyKey
        slotCount
        claimedSlots {
          runId
          stepKey
        }
        pendingSteps {
          runId
          stepKey
          enqueuedTimestamp
          assignedTimestamp
          priority
        }
      }
    }
  }
`;

const RowGrid = styled(Box)`
  display: grid;
  grid-template-columns: ${TEMPLATE_COLUMNS};
  height: 100%;
`;
