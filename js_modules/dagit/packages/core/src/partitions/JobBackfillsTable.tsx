import {gql, useQuery} from '@apollo/client';
import {Box, CursorPaginationControls, CursorPaginationProps, NonIdealState} from '@dagster-io/ui';
import React from 'react';

import {BackfillTable, BACKFILL_TABLE_FRAGMENT} from '../instance/BackfillTable';
import {RepositorySelector} from '../types/globalTypes';
import {Loading} from '../ui/Loading';

const BACKFILL_PAGE_SIZE = 10;

export const JobBackfillsTable = ({
  partitionSetName,
  partitionNames,
  repositorySelector,
  refetchCounter,
}: {
  partitionSetName: string;
  partitionNames: string[];
  repositorySelector: RepositorySelector;
  refetchCounter: number;
}) => {
  const [cursorStack, setCursorStack] = React.useState<string[]>(() => []);
  const [cursor, setCursor] = React.useState<string | undefined>();
  const queryResult = useQuery(JOB_BACKFILLS_QUERY, {
    variables: {
      partitionSetName,
      repositorySelector,
      cursor,
      limit: BACKFILL_PAGE_SIZE,
    },
    partialRefetch: true,
  });

  const refetch = queryResult.refetch;
  React.useEffect(() => {
    refetchCounter && refetch();
  }, [refetch, refetchCounter]);

  return (
    <Loading queryResult={queryResult}>
      {({partitionSetOrError}) => {
        const {backfills, pipelineName} = partitionSetOrError;

        if (!backfills.length) {
          return (
            <Box margin={{vertical: 20}}>
              <NonIdealState title={`No backfills for ${pipelineName}`} icon="no-results" />
            </Box>
          );
        }

        const paginationProps: CursorPaginationProps = {
          hasPrevCursor: !!cursor,
          hasNextCursor: backfills && backfills.length === BACKFILL_PAGE_SIZE,
          popCursor: () => {
            const nextStack = [...cursorStack];
            setCursor(nextStack.pop());
            setCursorStack(nextStack);
          },
          advanceCursor: () => {
            if (cursor) {
              setCursorStack((current) => [...current, cursor]);
            }
            const nextCursor = backfills && backfills[backfills.length - 1].backfillId;
            if (!nextCursor) {
              return;
            }
            setCursor(nextCursor);
          },
          reset: () => {
            setCursorStack([]);
            setCursor(undefined);
          },
        };
        return (
          <>
            <BackfillTable
              backfills={backfills}
              refetch={refetch}
              showBackfillTarget={false}
              allPartitions={partitionNames}
            />
            <CursorPaginationControls {...paginationProps} />
          </>
        );
      }}
    </Loading>
  );
};

const JOB_BACKFILLS_QUERY = gql`
  query JobBackfillsQuery(
    $partitionSetName: String!
    $repositorySelector: RepositorySelector!
    $cursor: String
    $limit: Int
  ) {
    partitionSetOrError(
      repositorySelector: $repositorySelector
      partitionSetName: $partitionSetName
    ) {
      ... on PartitionSet {
        id
        pipelineName
        backfills(cursor: $cursor, limit: $limit) {
          ...BackfillTableFragment
        }
      }
    }
  }
  ${BACKFILL_TABLE_FRAGMENT}
`;
