import {
  Box,
  CursorPaginationControls,
  CursorPaginationProps,
  NonIdealState,
} from '@dagster-io/ui-components';
import {useEffect, useState} from 'react';

import {gql, useQuery} from '../apollo-client';
import {JobBackfillsQuery, JobBackfillsQueryVariables} from './types/JobBackfillsTable.types';
import {RepositorySelector} from '../graphql/types';
import {BACKFILL_TABLE_FRAGMENT, BackfillTable} from '../instance/backfill/BackfillTable';
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
  const [cursorStack, setCursorStack] = useState<string[]>(() => []);
  const [cursor, setCursor] = useState<string | undefined>();
  const queryResult = useQuery<JobBackfillsQuery, JobBackfillsQueryVariables>(JOB_BACKFILLS_QUERY, {
    variables: {
      partitionSetName,
      repositorySelector,
      cursor,
      limit: BACKFILL_PAGE_SIZE,
    },
  });

  const refetch = queryResult.refetch;
  useEffect(() => {
    if (refetchCounter) {
      refetch();
    }
  }, [refetch, refetchCounter]);

  return (
    <Loading queryResult={queryResult}>
      {({partitionSetOrError}) => {
        if (partitionSetOrError.__typename === 'PartitionSetNotFoundError') {
          return (
            <Box margin={{vertical: 20}}>
              <NonIdealState title="Partition set not found." icon="no-results" />
            </Box>
          );
        }

        if (partitionSetOrError.__typename === 'PythonError') {
          return (
            <Box margin={{vertical: 20}}>
              <NonIdealState title="An error occurred." icon="no-results" />
            </Box>
          );
        }

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
            // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
            const nextCursor = backfills && backfills[backfills.length - 1]!.id;
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
          id
          ...BackfillTableFragment
        }
      }
    }
  }

  ${BACKFILL_TABLE_FRAGMENT}
`;
