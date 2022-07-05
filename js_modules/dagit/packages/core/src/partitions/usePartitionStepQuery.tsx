import {gql, useApolloClient, ApolloClient} from '@apollo/client';
import * as React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment';
import {DagsterTag} from '../runs/RunTag';
import {RunFilterToken} from '../runs/RunsFilterInput';
import {RunStatus} from '../types/globalTypes';

import {PartitionMatrixStepRunFragment} from './types/PartitionMatrixStepRunFragment';
import {
  PartitionStepLoaderQuery,
  PartitionStepLoaderQueryVariables,
} from './types/PartitionStepLoaderQuery';
import {PartitionRuns, PARTITION_MATRIX_STEP_RUN_FRAGMENT} from './useMatrixData';

interface DataState {
  runs: PartitionMatrixStepRunFragment[];
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
export function usePartitionStepQuery(
  partitionSetName: string,
  partitionNames: string[],
  pageSize: number,
  runsFilter: RunFilterToken[],
  jobName?: string,
  offset?: number,
  skipQuery?: boolean,
) {
  const client = useApolloClient();

  const version = React.useRef(0);
  const [dataState, setDataState] = React.useState<DataState>(InitialDataState);
  const _serializedRunTags = React.useMemo(
    () =>
      JSON.stringify(
        runsFilter.map((token) => {
          const [key, value] = token.value.split('=');
          return {key, value};
        }),
      ),
    [runsFilter],
  );

  React.useEffect(() => {
    // Note: there are several async steps to the loading process - to cancel the previous
    // invocation, we bump a version number that is captured in a local variable.
    // eg: If version.current no longer === v, this should stop updating state and exit.
    const v = version.current + 1;
    version.current = v;

    const runTags = JSON.parse(_serializedRunTags);
    setDataState((dataState) => ({...dataState, runs: [], loading: true}));

    const run = async () => {
      if (version.current !== v) {
        return;
      }
      let loadingCursorIdx = partitionNames.length - (offset || 0);
      const stopIdx = Math.max(0, loadingCursorIdx - pageSize);
      setDataState((state) => ({...state, partitionNames, loadingCursorIdx}));

      // Load runs in each of these partitions incrementally, running several queries in parallel
      // to maximize the throughput we can achieve from the GraphQL interface.
      const parallelQueries = 5;

      while (loadingCursorIdx > stopIdx) {
        const nextCursorIdx = Math.max(loadingCursorIdx - parallelQueries, 0);
        const sliceNames = partitionNames.slice(nextCursorIdx, loadingCursorIdx);
        const fetched = await Promise.all(
          sliceNames.map((partitionName) => {
            const partitionSetTag = {key: DagsterTag.PartitionSet, value: partitionSetName};
            const partitionTag = {key: DagsterTag.Partition, value: partitionName};
            // for jobs, filter by pipelineName/jobName instead of by partition set tag.  This
            // preserves partition run history across the pipeline => job transition
            const runTagsFilter = jobName
              ? {
                  pipelineName: jobName,
                  tags: [...runTags, partitionTag],
                }
              : {tags: [...runTags, partitionTag, partitionSetTag]};
            return fetchRunsForFilter(client, {limit: 1000, filter: runTagsFilter});
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

        setDataState((state) => ({...state, loading: true}));

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

    if (!skipQuery) {
      run();
    }

    return () => {
      version.current += 1;
    };
  }, [
    pageSize,
    client,
    partitionSetName,
    _serializedRunTags,
    jobName,
    offset,
    partitionNames,
    skipQuery,
  ]);

  return assemblePartitions(dataState);
}

async function fetchRunsForFilter(
  client: ApolloClient<any>,
  variables: PartitionStepLoaderQueryVariables,
) {
  const result = await client.query<PartitionStepLoaderQuery, PartitionStepLoaderQueryVariables>({
    fetchPolicy: 'network-only',
    query: PARTITION_STEP_LOADER_QUERY,
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

const PARTITION_STEP_LOADER_QUERY = gql`
  query PartitionStepLoaderQuery($filter: RunsFilter!, $cursor: String, $limit: Int) {
    pipelineRunsOrError(filter: $filter, cursor: $cursor, limit: $limit) {
      ... on Runs {
        results {
          id
          ...PartitionMatrixStepRunFragment
        }
      }
      ... on InvalidPipelineRunsFilterError {
        message
      }
      ...PythonErrorFragment
    }
  }
  ${PARTITION_MATRIX_STEP_RUN_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
