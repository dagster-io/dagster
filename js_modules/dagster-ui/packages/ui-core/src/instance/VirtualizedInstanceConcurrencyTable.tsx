import {Box, Icon, useDelayedState} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {useRef} from 'react';
import {Link} from 'react-router-dom';
import styles from './VirtualizedInstanceConcurrencyTable.module.css';

import {gql, useQuery} from '../apollo-client';
import {
  SingleConcurrencyKeyQuery,
  SingleConcurrencyKeyQueryVariables,
} from './types/VirtualizedInstanceConcurrencyTable.types';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {Container, HeaderCell, HeaderRow, Inner, Row, RowCell} from '../ui/VirtualizedTable';
import {LoadingOrNone} from '../workspace/VirtualizedWorkspaceTable';

const POOL_TEMPLATE_COLUMNS = '1fr 1fr';

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
  return (
    <HeaderRow templateColumns={POOL_TEMPLATE_COLUMNS} sticky>
      <HeaderCell>Pool</HeaderCell>
      <HeaderCell>Limit</HeaderCell>
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
      <Box 
        className={styles.rowGrid} 
        border="bottom" 
        style={{gridTemplateColumns: POOL_TEMPLATE_COLUMNS}}
      >
        <RowCell>
          <Box flex={{gap: 4, alignItems: 'center'}}>
            <Icon name="dynamic_feed" />
            <Link to={path}>{concurrencyKey}</Link>
          </Box>
        </RowCell>
        <RowCell>
          {limit ? <div>{limit.slotCount}</div> : <LoadingOrNone queryResult={queryResult} />}
        </RowCell>
      </Box>
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

