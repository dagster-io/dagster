import {gql, useApolloClient, ApolloClient} from '@apollo/client';
import * as React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment';
import {QueryPersistedStateConfig, useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {DagsterTag} from '../runs/RunTag';
import {RunFilterToken} from '../runs/RunsFilterInput';
import {RunStatus} from '../types/globalTypes';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {PARTITION_GRAPH_SET_RUN_FRAGMENT} from './PartitionGraphSet';
import {PARTITION_RUN_MATRIX_RUN_FRAGMENT} from './PartitionRunMatrix';
import {
  PartitionSetLoaderQuery,
  PartitionSetLoaderQueryVariables,
} from './types/PartitionSetLoaderQuery';
import {PartitionSetLoaderRunFragment} from './types/PartitionSetLoaderRunFragment';
import {
  PartitionSetNamesQuery,
  PartitionSetNamesQueryVariables,
} from './types/PartitionSetNamesQuery';

interface PaginationState {
  cursorStack: string[];
  cursor: string | null;
  pageSize: number | 'all';
}

export interface PartitionRuns {
  name: string;
  runsLoaded: boolean;
  runs: PartitionSetLoaderRunFragment[];
}

const PaginationStateQueryConfig: QueryPersistedStateConfig<PaginationState> = {
  encode: (state) => ({
    cursor: state.cursor || undefined,
    cursorStack: state.cursorStack.length ? state.cursorStack.join(',') : undefined,
    pageSize: state.pageSize,
  }),
  decode: (qs) => ({
    cursor: qs.cursor || null,
    cursorStack: qs.cursorStack ? qs.cursorStack.split(',') : [],
    pageSize: qs.pageSize === 'all' ? 'all' : Number(qs.pageSize || 30),
  }),
};

interface DataState {
  runs: PartitionSetLoaderRunFragment[];
  partitionNames: string[];
  loading: boolean;
  loadingCursorIdx: number;
  error?: PythonErrorFragment;
}

const InitialDataState: DataState = {
  runs: [],
  partitionNames: [],
  loading: false,
  loadingCursorIdx: 0,
};

/**
 * This React hook mirrors `useCursorPaginatedQuery` but collects each page of partitions
 * in slices that are smaller than pageSize and cause the results to load incrementally.
 */
export function useChunkedPartitionsQuery(
  partitionSetName: string,
  runsFilter: RunFilterToken[],
  repoAddress: RepoAddress,
  jobName?: string,
) {
  const repositorySelector = repoAddressToSelector(repoAddress);
  const client = useApolloClient();

  const version = React.useRef(0);
  const [dataState, setDataState] = React.useState<DataState>(InitialDataState);

  const [{cursor, cursorStack, pageSize}, setPaginationState] = useQueryPersistedState(
    PaginationStateQueryConfig,
  );

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
          cursor,
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
      let loadingCursorIdx = partitionNames.length;

      if (
        namesResult.data.partitionSetOrError.__typename === 'PartitionSet' &&
        namesResult.data.partitionSetOrError.partitionsOrError.__typename === 'PythonError'
      ) {
        const partitionSet = namesResult.data.partitionSetOrError;
        const error =
          partitionSet.partitionsOrError.__typename === 'PythonError'
            ? partitionSet.partitionsOrError
            : undefined;
        setDataState((state) => ({...state, error, loadingCursorIdx, partitionNames}));
      } else {
        setDataState((state) => ({...state, partitionNames, loadingCursorIdx}));
      }

      // Load runs in each of these partitions incrementally, running several queries in parallel
      // to maximize the throughput we can achieve from the GraphQL interface.
      const parallelQueries = 5;

      while (loadingCursorIdx > 0) {
        const nextCursorIdx = Math.max(loadingCursorIdx - parallelQueries, 0);
        const sliceNames = partitionNames.slice(nextCursorIdx, loadingCursorIdx);
        const fetched = await Promise.all(
          sliceNames.map((partitionName) => {
            const partitionSetTag = {key: DagsterTag.PartitionSet, value: partitionSetName};
            const partitionTag = {key: DagsterTag.Partition, value: partitionName};
            // for jobs, filter by pipelineName/jobName instead of by partition set tag.  This
            // preserves partition run history across the pipeline => job transition
            const runsFilter = jobName
              ? {
                  pipelineName: jobName,
                  tags: [...runTags, partitionTag],
                }
              : {tags: [...runTags, partitionTag, partitionSetTag]};
            return fetchRunsForFilter(client, {limit: 1000, filter: runsFilter});
          }),
        );
        if (version.current !== v) {
          return;
        }

        loadingCursorIdx = nextCursorIdx;
        setDataState((state) => ({
          ...state,
          runs: [...state.runs].concat(...fetched),
          loading: loadingCursorIdx > 0,
          loadingCursorIdx,
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
            statuses: [RunStatus.STARTED],
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
  }, [pageSize, cursor, client, partitionSetName, runsFilter, repositorySelector, jobName]);

  // Note: cursor === null is page zero and cursors specify subsequent pages.
  const {loading, loadingCursorIdx, partitionNames, error} = dataState;
  const loadingPercent =
    0.05 + 0.95 * ((partitionNames.length - loadingCursorIdx) / partitionNames.length);

  return {
    loading,
    loadingPercent,
    partitions: assemblePartitions(dataState),
    error,
    pageSize,
    setPageSize: (pageSize: number | 'all') => {
      setPaginationState({cursor: null, cursorStack: [], pageSize});
    },
    paginationProps: {
      hasPrevCursor: cursor !== null,
      hasNextCursor: partitionNames.length >= pageSize,
      popCursor: () => {
        if (cursor === null) {
          return;
        }
        setDataState({
          loading: false,
          loadingCursorIdx: 0,
          partitionNames: [],
          runs: [],
        });
        setPaginationState({
          pageSize,
          cursorStack: cursorStack.slice(0, cursorStack.length - 1),
          cursor: cursorStack.length ? cursorStack[cursorStack.length - 1] : null,
        });
      },
      advanceCursor: () => {
        setDataState({
          loading: false,
          loadingCursorIdx: 0,
          partitionNames: [],
          runs: [],
        });
        setPaginationState({
          pageSize,
          cursorStack: cursor ? [...cursorStack, cursor] : cursorStack,
          cursor: dataState.partitionNames[0],
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
    (result.data.pipelineRunsOrError.__typename === 'Runs' &&
      result.data.pipelineRunsOrError.results) ||
    []
  );
}

function assemblePartitions(data: DataState) {
  // Note: Partitions don't have any unique keys beside their names, so we use names
  // extensively in our display layer as React keys. To create unique empty partitions
  // we use different numbers of zero-width space characters
  const results: PartitionRuns[] = [];
  const byName: {[name: string]: PartitionRuns} = {};

  data.partitionNames.forEach((name, idx) => {
    byName[name] = {
      name,
      runsLoaded: idx >= data.loadingCursorIdx,
      runs: [],
    };
    results.push(byName[name]);
  });

  data.runs.forEach((r) => {
    const partitionName = r.tags.find((t) => t.key === DagsterTag.Partition)?.value || '';
    byName[partitionName]?.runs.push(r);
  });

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
  query PartitionSetLoaderQuery($filter: RunsFilter!, $cursor: String, $limit: Int) {
    pipelineRunsOrError(filter: $filter, cursor: $cursor, limit: $limit) {
      ... on Runs {
        results {
          id
          ...PartitionSetLoaderRunFragment
        }
      }
      ... on InvalidPipelineRunsFilterError {
        message
      }
      ...PythonErrorFragment
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
          ...PythonErrorFragment
        }
      }
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
