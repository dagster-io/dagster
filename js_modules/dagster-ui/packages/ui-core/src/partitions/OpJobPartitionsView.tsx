import {
  Box,
  Button,
  Dialog,
  Icon,
  NonIdealState,
  Spinner,
  Subheading,
  Tooltip,
  useViewport,
} from '@dagster-io/ui-components';
import React, {useCallback, useEffect, useLayoutEffect, useMemo, useState} from 'react';

import {BackfillPartitionSelector} from './BackfillSelector';
import {JobBackfillsTable} from './JobBackfillsTable';
import {PartitionGraph} from './PartitionGraph';
import {PartitionStatus} from './PartitionStatus';
import {PartitionPerOpStatus, getVisibleItemCount} from './PartitionStepStatus';
import {GRID_FLOATING_CONTAINER_WIDTH} from './RunMatrixUtils';
import {
  OpJobPartitionSetFragment,
  OpJobPartitionStatusFragment,
  PartitionsStatusQuery,
  PartitionsStatusQueryVariables,
} from './types/OpJobPartitionsView.types';
import {PartitionRuns} from './useMatrixData';
import {usePartitionStepQuery} from './usePartitionStepQuery';
import {QueryResult, gql, useQuery} from '../apollo-client';
import {usePermissionsForLocation} from '../app/Permissions';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {RunStatus} from '../graphql/types';
import {DagsterTag} from '../runs/RunTag';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

type PartitionStatus = OpJobPartitionStatusFragment;

const simpleCache = new Map<
  string,
  QueryResult<PartitionsStatusQuery, PartitionsStatusQueryVariables>
>();

export const OpJobPartitionsView = React.memo(
  ({partitionSetName, repoAddress}: {partitionSetName: string; repoAddress: RepoAddress}) => {
    const repositorySelector = repoAddressToSelector(repoAddress);
    const variables = useMemo(
      () => ({partitionSetName, repositorySelector}),
      [partitionSetName, repositorySelector],
    );
    const cacheKey = useMemo(() => JSON.stringify(variables), [variables]);
    const cachedResult = useMemo(() => simpleCache.get(cacheKey), [cacheKey]);
    const currentQueryResult = useQuery<PartitionsStatusQuery, PartitionsStatusQueryVariables>(
      PARTITIONS_STATUS_QUERY,
      {
        variables: {partitionSetName, repositorySelector},
        notifyOnNetworkStatusChange: true,
        fetchPolicy: 'no-cache',
      },
    );

    useLayoutEffect(() => {
      if (currentQueryResult) {
        simpleCache.set(cacheKey, currentQueryResult);
      }
    }, [cacheKey, currentQueryResult]);
    const queryResult = currentQueryResult.data
      ? currentQueryResult
      : (cachedResult ?? currentQueryResult);
    const {data, loading} = queryResult;

    if (!data) {
      if (loading) {
        return (
          <Box padding={32} flex={{direction: 'column', alignItems: 'center'}}>
            <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
              <Spinner purpose="body-text" />
              <div>Loading partitions…</div>
            </Box>
          </Box>
        );
      }

      return (
        <Box padding={32}>
          <NonIdealState
            icon="error"
            title="An error occurred"
            description="An unexpected error occurred."
          />
        </Box>
      );
    }

    const {partitionSetOrError} = data;
    if (partitionSetOrError.__typename === 'PartitionSetNotFoundError') {
      return (
        <Box padding={32}>
          <NonIdealState
            icon="search"
            title="Partition set not found"
            description={partitionSetOrError.message}
          />
        </Box>
      );
    }

    if (partitionSetOrError.__typename === 'PythonError') {
      return (
        <Box padding={32}>
          <PythonErrorInfo error={partitionSetOrError} />
        </Box>
      );
    }

    if (partitionSetOrError.partitionsOrError.__typename === 'PythonError') {
      return (
        <Box padding={32}>
          <PythonErrorInfo error={partitionSetOrError.partitionsOrError} />
        </Box>
      );
    }

    const partitionNames = partitionSetOrError.partitionsOrError.results.map(({name}) => name);

    return (
      <OpJobPartitionsViewContent
        partitionNames={partitionNames}
        partitionSet={partitionSetOrError}
        repoAddress={repoAddress}
        partitionsQueryResult={currentQueryResult}
      />
    );
  },
);

export function usePartitionDurations(partitions: PartitionRuns[]) {
  return useMemo(() => {
    const stepDurationData: {[name: string]: {[key: string]: (number | undefined)[]}} = {};
    const runDurationData: {[name: string]: number | undefined} = {};

    partitions.forEach((p) => {
      if (!p.runsLoaded || p.runs.length === 0) {
        return;
      }
      const sortedRuns = p.runs.sort((a, b) => a.startTime || 0 - (b.startTime || 0));
      const lastRun = sortedRuns[sortedRuns.length - 1]!;
      stepDurationData[p.name] = {};
      runDurationData[p.name] =
        lastRun?.endTime && lastRun?.startTime ? lastRun.endTime - lastRun.startTime : undefined;

      lastRun.stepStats.forEach((s) => {
        stepDurationData[p.name]![s.stepKey] = [
          s.endTime && s.startTime ? s.endTime - s.startTime : undefined,
        ];
      });
    });

    return {runDurationData, stepDurationData};
  }, [partitions]);
}

export const OpJobPartitionsViewContent = React.memo(
  ({
    partitionSet,
    partitionNames,
    repoAddress,
    partitionsQueryResult,
  }: {
    partitionNames: string[];
    partitionSet: OpJobPartitionSetFragment;
    repoAddress: RepoAddress;
    partitionsQueryResult: QueryResult<PartitionsStatusQuery, PartitionsStatusQueryVariables>;
  }) => {
    const {
      permissions: {canLaunchPartitionBackfill},
      disabledReasons,
    } = usePermissionsForLocation(repoAddress.location);
    const {viewport, containerProps} = useViewport();

    const [pageSize, setPageSize] = useState(60);
    const [offset, setOffset] = useState<number>(0);
    const [showSteps, setShowSteps] = useState(false);
    const [showBackfillSetup, setShowBackfillSetup] = useState(false);
    const [blockDialog, setBlockDialog] = useState(false);
    const repositorySelector = repoAddressToSelector(repoAddress);
    const [backfillRefetchCounter, setBackfillRefetchCounter] = useState(0);

    const partitions = usePartitionStepQuery({
      partitionSetName: partitionSet.name,
      partitionTagName: DagsterTag.Partition,
      partitionNames,
      pageSize,
      runsFilter: [],
      repositorySelector,
      jobName: partitionSet.pipelineName,
      offset,
      skipQuery: !showSteps,
    });

    useEffect(() => {
      if (viewport.width && !showSteps) {
        // magical numbers to approximate the size of the window, which is calculated in the step
        // status component.  This approximation is to make sure that the window does not jump as
        // the pageSize gets recalculated
        const approxPageSize = getVisibleItemCount(viewport.width - GRID_FLOATING_CONTAINER_WIDTH);
        setPageSize(approxPageSize);
      }
    }, [viewport.width, showSteps, setPageSize]);

    const selectedPartitions = useMemo(() => {
      return showSteps
        ? partitionNames.slice(
            Math.max(0, partitionNames.length - 1 - offset - pageSize),
            partitionNames.length - offset,
          )
        : partitionNames;
    }, [offset, pageSize, partitionNames, showSteps]);

    const stepDurationData = usePartitionDurations(partitions).stepDurationData;

    const onSubmit = useCallback(() => setBlockDialog(true), []);

    const selectPartitionNamesSet = useMemo(
      () => new Set(selectedPartitions),
      [selectedPartitions],
    );

    const {partitionStatusesOrError} = partitionSet;
    const partitionStatuses = useMemo(() => {
      return partitionStatusesOrError.__typename === 'PartitionStatuses'
        ? partitionStatusesOrError.results
        : [];
    }, [partitionStatusesOrError]);

    const {runStatusData, runDurationData} = useMemo(() => {
      // Note: This view reads "run duration" from the `partitionStatusesOrError` GraphQL API,
      // rather than looking at the duration of the most recent run returned in `partitions` above
      // so that the latter can be loaded when you click "Show per-step status" only.
      const runStatusData: {[name: string]: RunStatus} = {};
      const runDurationData: {[name: string]: number | undefined} = {};

      partitionStatuses.forEach((p) => {
        runStatusData[p.partitionName] = p.runStatus || RunStatus.NOT_STARTED;
        if (selectPartitionNamesSet.has(p.partitionName)) {
          runDurationData[p.partitionName] = p.runDuration || undefined;
        }
      });
      return {runStatusData, runDurationData};
    }, [partitionStatuses, selectPartitionNamesSet]);

    const health = useMemo(() => {
      return {runStatusForPartitionKey: (name: string) => runStatusData[name]};
    }, [runStatusData]);

    return (
      <div>
        <Dialog
          canEscapeKeyClose={!blockDialog}
          canOutsideClickClose={!blockDialog}
          onClose={() => setShowBackfillSetup(false)}
          style={{width: 800, zIndex: 1000}}
          title={`Launch ${partitionSet.pipelineName} backfill`}
          isOpen={showBackfillSetup}
        >
          {showBackfillSetup && (
            <BackfillPartitionSelector
              partitionSetName={partitionSet.name}
              partitionNames={partitionNames}
              runStatusData={runStatusData}
              refreshing={partitionsQueryResult.loading}
              pipelineName={partitionSet.pipelineName}
              onCancel={() => setShowBackfillSetup(false)}
              onLaunch={(_backfillId, _stepQuery) => {
                setBackfillRefetchCounter(backfillRefetchCounter + 1);
                setShowBackfillSetup(false);
              }}
              onSubmit={onSubmit}
              repoAddress={repoAddress}
            />
          )}
        </Dialog>

        <Box
          flex={{justifyContent: 'space-between', direction: 'row', alignItems: 'center'}}
          border="bottom"
          padding={{vertical: 16, horizontal: 24}}
        >
          <Subheading>Status</Subheading>
          <Box flex={{gap: 8}}>
            <Button onClick={() => setShowSteps(!showSteps)}>
              {showSteps ? 'Hide per-step status' : 'Show per-step status'}
            </Button>
            <Button
              onClick={() => partitionsQueryResult.refetch()}
              loading={partitionsQueryResult.loading}
              disabled={partitionsQueryResult.loading}
            >
              Refresh
            </Button>
            {canLaunchPartitionBackfill ? (
              <Button
                icon={<Icon name="add_circle" />}
                onClick={() => {
                  void partitionsQueryResult.refetch();
                  setShowBackfillSetup(!showBackfillSetup);
                }}
              >
                Launch backfill…
              </Button>
            ) : (
              <Tooltip content={disabledReasons.canLaunchPartitionBackfill}>
                <Button icon={<Icon name="add_circle" />} disabled>
                  Launch backfill…
                </Button>
              </Tooltip>
            )}
          </Box>
        </Box>
        <Box flex={{direction: 'row', alignItems: 'center'}} border="bottom" padding={{left: 8}}>
          <CountBox count={partitionNames.length} label="Total partitions" />
          <CountBox
            count={useMemo(
              () => partitionNames.filter((x) => runStatusData[x] === RunStatus.FAILURE).length,
              [partitionNames, runStatusData],
            )}
            label="Failed partitions"
          />
          <CountBox
            count={useMemo(
              () =>
                partitionNames.filter(
                  (x) => !runStatusData[x] || runStatusData[x] === RunStatus.NOT_STARTED,
                ).length,
              [partitionNames, runStatusData],
            )}
            label="Missing partitions"
          />
        </Box>
        <Box padding={{vertical: 16, horizontal: 24}}>
          <div {...containerProps}>
            <PartitionStatus
              partitionNames={partitionNames}
              health={health}
              selected={showSteps ? selectedPartitions : undefined}
              selectionWindowSize={pageSize}
              onClick={useCallback(
                (partitionName: string) => {
                  const maxIdx = partitionNames.length - 1;
                  const selectedIdx = partitionNames.indexOf(partitionName);
                  const nextOffset = Math.min(
                    maxIdx,
                    Math.max(0, maxIdx - selectedIdx - 0.5 * pageSize),
                  );
                  setOffset(nextOffset);
                  if (!showSteps) {
                    setShowSteps(true);
                  }
                },
                [pageSize, partitionNames, showSteps],
              )}
              tooltipMessage="Click to view per-step status"
            />
          </div>
          {showSteps ? (
            <Box margin={{top: 16}}>
              <PartitionPerOpStatus
                partitionNames={partitionNames}
                partitions={partitions}
                pipelineName={partitionSet.pipelineName}
                repoAddress={repoAddress}
                setPageSize={setPageSize}
                offset={offset}
                setOffset={setOffset}
              />
            </Box>
          ) : null}
        </Box>
        <Box padding={{horizontal: 24, vertical: 16}} border="top-and-bottom">
          <Subheading>Run duration</Subheading>
        </Box>
        <Box margin={24}>
          <PartitionGraph
            isJob={true}
            title="Execution time by partition"
            yLabel="Execution time (secs)"
            partitionNames={showSteps ? selectedPartitions : partitionNames}
            jobDataByPartition={runDurationData}
          />
        </Box>
        {showSteps ? (
          <>
            <Box padding={{horizontal: 24, vertical: 16}}>
              <Subheading>Step duration</Subheading>
            </Box>
            <Box margin={24}>
              <PartitionGraph
                isJob={true}
                title="Execution time by partition"
                yLabel="Execution time (secs)"
                partitionNames={selectedPartitions}
                stepDataByPartition={stepDurationData}
              />
            </Box>
          </>
        ) : null}
        <Box
          padding={{horizontal: 24, vertical: 16}}
          border="top-and-bottom"
          style={{marginBottom: -1}}
        >
          <Subheading>Backfill history</Subheading>
        </Box>
        <Box margin={{bottom: 20}}>
          <JobBackfillsTable
            partitionSetName={partitionSet.name}
            repositorySelector={repositorySelector}
            partitionNames={partitionNames}
            refetchCounter={backfillRefetchCounter}
          />
        </Box>
      </div>
    );
  },
);

export const CountBox = ({count, label}: {count: number; label: string}) => (
  <Box padding={16} style={{flex: 1}} border="right">
    <div style={{fontSize: 18, marginBottom: 4}}>
      <strong>{count}</strong>
    </div>
    <div>{label}</div>
  </Box>
);

const PARTITIONS_STATUS_QUERY = gql`
  query PartitionsStatusQuery(
    $partitionSetName: String!
    $repositorySelector: RepositorySelector!
  ) {
    partitionSetOrError(
      repositorySelector: $repositorySelector
      partitionSetName: $partitionSetName
    ) {
      ... on PartitionSet {
        id
        ...OpJobPartitionSet
      }
      ... on PartitionSetNotFoundError {
        message
      }
      ...PythonErrorFragment
    }
  }

  fragment OpJobPartitionSet on PartitionSet {
    id
    name
    pipelineName
    partitionsOrError {
      ... on Partitions {
        results {
          name
        }
      }
      ...PythonErrorFragment
    }
    partitionStatusesOrError {
      ... on PartitionStatuses {
        results {
          id
          ...OpJobPartitionStatus
        }
      }
      ...PythonErrorFragment
    }
  }

  fragment OpJobPartitionStatus on PartitionStatus {
    id
    partitionName
    runStatus
    runDuration
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
