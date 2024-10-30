import {
  Box,
  Button,
  ButtonLink,
  Icon,
  Menu,
  MenuItem,
  Popover,
  Tag,
  useDelayedState,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {useRef} from 'react';
import styled from 'styled-components';

import {gql, useQuery} from '../apollo-client';
import {
  SingleConcurrencyKeyQuery,
  SingleConcurrencyKeyQueryVariables,
} from './types/VirtualizedInstanceConcurrencyTable.types';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {Container, HeaderCell, HeaderRow, Inner, Row, RowCell} from '../ui/VirtualizedTable';
import {LoadingOrNone} from '../workspace/VirtualizedWorkspaceTable';

const TEMPLATE_COLUMNS = '1fr 150px 150px 150px 150px 150px';

export const ConcurrencyTable = ({
  concurrencyKeys,
  onEdit,
  onDelete,
  onSelect,
}: {
  concurrencyKeys: string[];
  onEdit: (key: string) => void;
  onDelete: (key: string) => void;
  onSelect: (key: string | undefined) => void;
}) => {
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
                onEdit={onEdit}
                onDelete={onDelete}
                onSelect={onSelect}
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
    <HeaderRow templateColumns={TEMPLATE_COLUMNS} sticky>
      <HeaderCell>Concurrency key</HeaderCell>
      <HeaderCell>Total slots</HeaderCell>
      <HeaderCell>Assigned steps</HeaderCell>
      <HeaderCell>Pending steps</HeaderCell>
      <HeaderCell>All steps</HeaderCell>
      <HeaderCell></HeaderCell>
    </HeaderRow>
  );
};
const ConcurrencyRow = ({
  concurrencyKey,
  onEdit,
  onDelete,
  onSelect,
  height,
  start,
}: {
  concurrencyKey: string;
  onDelete: (key: string) => void;
  onEdit: (key: string) => void;
  onSelect: (key: string | undefined) => void;
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

  return (
    <Row $height={height} $start={start}>
      <RowGrid border="bottom">
        <RowCell>
          <>{concurrencyKey}</>
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
              <Tag intent="primary" interactive>
                <ButtonLink
                  onClick={() => {
                    onSelect(limit.concurrencyKey);
                  }}
                >
                  View all
                </ButtonLink>
              </Tag>
            </Box>
          ) : (
            <LoadingOrNone queryResult={queryResult} />
          )}
        </RowCell>
        <RowCell>
          <ConcurrencyLimitActionMenu
            concurrencyKey={concurrencyKey}
            onEdit={onEdit}
            onDelete={onDelete}
          />
        </RowCell>
      </RowGrid>
    </Row>
  );
};

const ConcurrencyLimitActionMenu = ({
  concurrencyKey,
  onDelete,
  onEdit,
}: {
  concurrencyKey: string;
  onEdit: (key: string) => void;
  onDelete: (key: string) => void;
}) => {
  return (
    <Popover
      content={
        <Menu>
          <MenuItem icon="edit" text="Edit" onClick={() => onEdit(concurrencyKey)} />
          <MenuItem
            icon="delete"
            intent="danger"
            text="Delete"
            onClick={() => onDelete(concurrencyKey)}
          />
        </Menu>
      }
      position="bottom-left"
    >
      <Button icon={<Icon name="expand_more" />} />
    </Popover>
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
