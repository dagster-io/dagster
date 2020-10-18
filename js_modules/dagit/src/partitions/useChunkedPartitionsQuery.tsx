import gql from 'graphql-tag';
import * as React from 'react';
import {useApolloClient} from 'react-apollo';

import {useRepositorySelector} from 'src/DagsterRepositoryContext';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {
  PartitionLongitudinalQuery,
  PartitionLongitudinalQueryVariables,
  PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results,
} from 'src/partitions/types/PartitionLongitudinalQuery';
import {RunTable} from 'src/runs/RunTable';

type Partition = PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results;

interface DataState {
  results: Partition[];
  loading: boolean;
  cursorStack: string[];
  cursor: string | null;
}

const InitialDataState: DataState = {results: [], cursor: null, cursorStack: [], loading: false};

/**
 * This React hook mirrors `useCursorPaginatedQuery` but collects each page of partitions
 * in slices that are smaller than pageSize and cause the results to load incrementally.
 */
export function useChunkedPartitionsQuery(partitionSetName: string, pageSize: number) {
  const {repositoryName, repositoryLocationName} = useRepositorySelector();
  const client = useApolloClient();

  const version = React.useRef(0);
  const [dataState, setDataState] = React.useState<DataState>(InitialDataState);
  const {cursor, loading, results, cursorStack} = dataState;

  React.useEffect(() => {
    const v = version.current + 1;
    version.current = v;

    setDataState((dataState) => ({...dataState, results: [], loading: true}));

    let c = cursor;
    let accumulated: Partition[] = [];
    const fetchOne = async () => {
      const result = await client.query<
        PartitionLongitudinalQuery,
        PartitionLongitudinalQueryVariables
      >({
        fetchPolicy: 'network-only',
        query: PARTITION_SET_QUERY,
        variables: {
          partitionSetName,
          repositorySelector: {repositoryName, repositoryLocationName},
          reverse: true,
          cursor: c,
          limit: Math.min(2, pageSize - accumulated.length),
        },
      });
      if (version.current !== v) {
        return;
      }
      const fetched = partitionsFromResult(result.data);
      accumulated = [...fetched, ...accumulated];
      const more = accumulated.length < pageSize && fetched.length > 0;

      setDataState((dataState) => ({...dataState, results: accumulated, loading: more}));

      if (more) {
        c = accumulated[0].name;
        fetchOne();
      }
    };

    fetchOne();
  }, [pageSize, cursor, client, partitionSetName, repositoryName, repositoryLocationName]);

  // Note: cursor === null is page zero and cursors specify subsequent pages.

  return {
    loading,
    partitions: [...buildEmptyPartitions(pageSize - results.length), ...results],
    paginationProps: {
      hasPrevCursor: cursor !== null,
      hasNextCursor: results.length >= pageSize,
      popCursor: () => {
        if (cursor === null) {
          return;
        }
        setDataState({
          results: [],
          cursor: cursorStack.length ? cursorStack[cursorStack.length - 1] : null,
          cursorStack: cursorStack.slice(0, cursorStack.length - 1),
          loading: false,
        });
      },
      advanceCursor: () => {
        setDataState({
          loading: false,
          cursorStack: cursor ? [...cursorStack, cursor] : cursorStack,
          cursor: results[0].name,
          results: [],
        });
      },
      reset: () => {
        setDataState(InitialDataState);
      },
    },
  };
}

function buildEmptyPartitions(count: number) {
  // Note: Partitions don't have any unique keys beside their names, so we use names
  // extensively in our display layer as React keys. To create unique empty partitions
  // we use different numbers of zero-width space characters
  const empty: Partition[] = [];
  for (let ii = 0; ii < count; ii++) {
    empty.push({
      __typename: 'Partition',
      name: `\u200b`.repeat(ii + 1),
      runs: [],
    });
  }
  return empty;
}

function partitionsFromResult(result?: PartitionLongitudinalQuery) {
  if (result?.partitionSetOrError.__typename !== 'PartitionSet') {
    return [];
  }
  if (result.partitionSetOrError.partitionsOrError.__typename !== 'Partitions') {
    return [];
  }
  return result.partitionSetOrError.partitionsOrError.results;
}

const PARTITION_SET_QUERY = gql`
  query PartitionLongitudinalQuery(
    $partitionSetName: String!
    $repositorySelector: RepositorySelector!
    $limit: Int
    $cursor: String
    $reverse: Boolean
  ) {
    partitionSetOrError(
      repositorySelector: $repositorySelector
      partitionSetName: $partitionSetName
    ) {
      ... on PartitionSet {
        name
        partitionsOrError(cursor: $cursor, limit: $limit, reverse: $reverse) {
          ... on Partitions {
            results {
              name
              runs {
                runId
                pipelineName
                tags {
                  key
                  value
                }
                stats {
                  __typename
                  ... on PipelineRunStatsSnapshot {
                    startTime
                    endTime
                    materializations
                  }
                }
                status
                stepStats {
                  __typename
                  stepKey
                  startTime
                  endTime
                  status
                  materializations {
                    __typename
                  }
                  expectationResults {
                    success
                  }
                }
                ...RunTableRunFragment
              }
            }
          }
          ... on PythonError {
            ...PythonErrorFragment
          }
        }
      }
    }
  }
  ${PythonErrorInfo.fragments.PythonErrorFragment}
  ${RunTable.fragments.RunTableRunFragment}
`;
