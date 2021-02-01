import {gql, useApolloClient, ApolloClient} from '@apollo/client';
import * as React from 'react';

import {PYTHON_ERROR_FRAGMENT} from 'src/app/PythonErrorInfo';
import {PARTITION_GRAPH_SET_RUN_FRAGMENT} from 'src/partitions/PartitionGraphSet';
import {PARTITION_RUN_MATRIX_RUN_FRAGMENT} from 'src/partitions/PartitionRunMatrix';
import {
  PartitionSetLoaderQuery,
  PartitionSetLoaderQueryVariables,
} from 'src/partitions/types/PartitionSetLoaderQuery';
import {PartitionSetLoaderRunFragment} from 'src/partitions/types/PartitionSetLoaderRunFragment';
import {
  PartitionSetNamesQuery,
  PartitionSetNamesQueryVariables,
} from 'src/partitions/types/PartitionSetNamesQuery';
import {DagsterTag} from 'src/runs/RunTag';
import {PipelineRunStatus} from 'src/types/globalTypes';
import {TokenizingFieldValue} from 'src/ui/TokenizingField';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';

interface DataState {
  runs: PartitionSetLoaderRunFragment[];
  partitionNames: string[];
  loading: boolean;
  loadingPercent: number;
  cursorStack: string[];
  cursor: string | null;
}

const InitialDataState: DataState = {
  runs: [],
  partitionNames: [],
  cursor: null,
  cursorStack: [],
  loading: false,
  loadingPercent: 0,
};

/**
 * This React hook mirrors `useCursorPaginatedQuery` but collects each page of partitions
 * in slices that are smaller than pageSize and cause the results to load incrementally.
 */
export function useChunkedPartitionsQuery(
  partitionSetName: string,
  pageSize: number | 'all',
  runsFilter: TokenizingFieldValue[],
  repoAddress: RepoAddress,
) {
  const repositorySelector = repoAddressToSelector(repoAddress);
  const client = useApolloClient();

  const version = React.useRef(0);
  const [dataState, setDataState] = React.useState<DataState>(InitialDataState);
  const {cursor, loading, loadingPercent, cursorStack} = dataState;

  React.useEffect(() => {
    // Note: there are several async steps to the loading process - to cancel the previous
    // invocation, we bump a version number that is captured in a local variable.
    // eg: If version.current no longer === v, this should stop updating state and exit.
    const v = version.current + 1;
    version.current = v;

    setDataState((dataState) => ({...dataState, runs: [], loading: true, loadingPercent: 0}));

    const runTags = runsFilter.map((token) => {
      const [key, value] = token.value.split('=');
      return {key, value};
    });

    const run = async () => {
      // Load the partition names in the current page range
      const namesResult = await client.query<
        PartitionSetNamesQuery,
        PartitionSetNamesQueryVariables
      >({
        fetchPolicy: 'network-only',
        query: PARTITION_SET_NAMES_QUERY,
        variables: {
          partitionSetName,
          repositorySelector,
          reverse: true,
          cursor: cursor,
          limit: pageSize === 'all' ? 100000 : pageSize,
        },
      });

      if (version.current !== v) {
        return;
      }
      const partitionNames =
        (namesResult.data.partitionSetOrError.__typename === 'PartitionSet' &&
          namesResult.data.partitionSetOrError.partitionsOrError.__typename === 'Partitions' &&
          namesResult.data.partitionSetOrError.partitionsOrError.results.map((r) => r.name)) ||
        [];

      setDataState((state) => ({...state, partitionNames, loadingPercent: 0.05}));

      // Load runs in each of these partitions incrementally, running several queries in parallel
      // to maximize the throughput we can achieve from the GraphQL interface.
      const parallelQueries = 5;
      for (let ii = partitionNames.length; ii >= 0; ii -= parallelQueries) {
        const sliceStartIdx = Math.max(ii - parallelQueries, 0);
        const sliceNames = partitionNames.slice(sliceStartIdx, ii);
        const fetched = await Promise.all(
          sliceNames.map((partitionName) =>
            fetchRunsForFilter(client, {
              limit: 1000,
              filter: {
                tags: [
                  ...runTags,
                  {key: DagsterTag.PartitionSet, value: partitionSetName},
                  {key: DagsterTag.Partition, value: partitionName},
                ],
              },
            }),
          ),
        );
        if (version.current !== v) {
          return;
        }
        setDataState((state) => ({
          ...state,
          runs: [...state.runs].concat(...fetched),
          loading: sliceStartIdx > 0,
          loadingPercent:
            0.05 + 0.95 * ((partitionNames.length - sliceStartIdx) / partitionNames.length),
        }));
      }

      // Periodically refresh pending runs and look for new runs in the displayed partitions.
      // Note: this timer is canceled when a subsequent invocation of the useEffect updates `version.current`,
      // because we don't want to create this interval until the initial load completes.

      const timer: NodeJS.Timeout = setInterval(async () => {
        if (version.current !== v) {
          return clearInterval(timer);
        }

        setDataState((state) => ({...state, loading: true, loadingPercent: 0}));

        // Fetch the 10 most recent runs for the pipeline so we pick up on new runs being launched.
        // Note: this may be insufficient but seems like it will handle the 99% case where runs
        // are either all queued (at the backfill start) or queued sequentially / slowly.
        const recent = await fetchRunsForFilter(client, {
          limit: 10,
          filter: {
            tags: [...runTags, {key: DagsterTag.PartitionSet, value: partitionSetName}],
          },
        });

        // Fetch runs in the partition set that are in the STARTED state, indicating active updates
        const pending = await fetchRunsForFilter(client, {
          filter: {
            statuses: [PipelineRunStatus.STARTED],
            tags: [...runTags, {key: DagsterTag.PartitionSet, value: partitionSetName}],
          },
        });

        if (version.current !== v) {
          return clearInterval(timer);
        }

        // Filter detected changes to just runs in our visible range of partitions, and then update
        // local state if changes have been found.
        const relevant = [...pending, ...recent].filter((run) =>
          run.tags.find((t) => t.key === DagsterTag.Partition && partitionNames.includes(t.value)),
        );
        setDataState((state) => {
          const updated = state.runs
            .filter((r) => !relevant.some((o) => o.runId === r.runId))
            .concat(relevant);
          return {...state, loading: false, runs: updated};
        });
      }, 10 * 1000);
    };

    run();

    return () => {
      version.current += 1;
    };
  }, [pageSize, cursor, client, partitionSetName, runsFilter, repositorySelector]);

  // Note: cursor === null is page zero and cursors specify subsequent pages.

  return {
    loading,
    loadingPercent,
    partitions: assemblePartitions(dataState),
    paginationProps: {
      hasPrevCursor: cursor !== null,
      hasNextCursor: dataState.partitionNames.length >= pageSize,
      popCursor: () => {
        if (cursor === null) {
          return;
        }
        setDataState({
          loading: false,
          loadingPercent: 0,
          cursorStack: cursorStack.slice(0, cursorStack.length - 1),
          cursor: cursorStack.length ? cursorStack[cursorStack.length - 1] : null,
          partitionNames: [],
          runs: [],
        });
      },
      advanceCursor: () => {
        setDataState({
          loading: false,
          loadingPercent: 0,
          cursorStack: cursor ? [...cursorStack, cursor] : cursorStack,
          cursor: dataState.partitionNames[0],
          partitionNames: [],
          runs: [],
        });
      },
      reset: () => {
        setDataState(InitialDataState);
      },
    },
  };
}

async function fetchRunsForFilter(
  client: ApolloClient<any>,
  variables: PartitionSetLoaderQueryVariables,
) {
  const result = await client.query<PartitionSetLoaderQuery, PartitionSetLoaderQueryVariables>({
    fetchPolicy: 'network-only',
    query: PARTITION_SET_LOADER_QUERY,
    variables,
  });
  return (
    (result.data.pipelineRunsOrError.__typename === 'PipelineRuns' &&
      result.data.pipelineRunsOrError.results) ||
    []
  );
}
function assemblePartitions(data: {
  partitionNames: string[];
  runs: PartitionSetLoaderRunFragment[];
}) {
  // Note: Partitions don't have any unique keys beside their names, so we use names
  // extensively in our display layer as React keys. To create unique empty partitions
  // we use different numbers of zero-width space characters
  const results: {
    __typename: 'Partition';
    name: string;
    runs: PartitionSetLoaderRunFragment[];
  }[] = [];
  for (const name of data.partitionNames) {
    results.push({
      __typename: 'Partition',
      name,
      runs: data.runs.filter((r) =>
        r.tags.some((t) => t.key === DagsterTag.Partition && t.value === name),
      ),
    });
  }
  return results;
}

const PARTITION_SET_LOADER_RUN_FRAGMENT = gql`
  fragment PartitionSetLoaderRunFragment on PipelineRun {
    id
    ...PartitionGraphSetRunFragment
    ...PartitionRunMatrixRunFragment
  }
  ${PARTITION_RUN_MATRIX_RUN_FRAGMENT}
  ${PARTITION_GRAPH_SET_RUN_FRAGMENT}
`;

const PARTITION_SET_LOADER_QUERY = gql`
  query PartitionSetLoaderQuery($filter: PipelineRunsFilter!, $cursor: String, $limit: Int) {
    pipelineRunsOrError(filter: $filter, cursor: $cursor, limit: $limit) {
      ... on PipelineRuns {
        results {
          id
          ...PartitionSetLoaderRunFragment
        }
      }
      ... on InvalidPipelineRunsFilterError {
        message
      }
      ... on PythonError {
        ...PythonErrorFragment
      }
    }
  }
  ${PARTITION_SET_LOADER_RUN_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

const PARTITION_SET_NAMES_QUERY = gql`
  query PartitionSetNamesQuery(
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
        id
        name
        partitionsOrError(cursor: $cursor, limit: $limit, reverse: $reverse) {
          ... on Partitions {
            results {
              name
            }
          }
        }
      }
    }
  }
`;
