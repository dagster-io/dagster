import {gql, useQuery} from '@apollo/client';
import {Box, Button, Dialog, Icon, Tooltip, Colors, Subheading, useViewport} from '@dagster-io/ui';
import * as React from 'react';

import {usePermissionsForLocation} from '../app/Permissions';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {RunStatus} from '../graphql/types';
import {DagsterTag} from '../runs/RunTag';
import {Loading} from '../ui/Loading';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {BackfillPartitionSelector} from './BackfillSelector';
import {JobBackfillsTable} from './JobBackfillsTable';
import {PartitionGraph} from './PartitionGraph';
import {PartitionStatus} from './PartitionStatus';
import {getVisibleItemCount, PartitionPerOpStatus} from './PartitionStepStatus';
import {GRID_FLOATING_CONTAINER_WIDTH} from './RunMatrixUtils';
import {
  OpJobPartitionSetFragment,
  OpJobPartitionStatusFragment,
  PartitionsStatusQuery,
  PartitionsStatusQueryVariables,
} from './types/OpJobPartitionsView.types';
import {PartitionRuns} from './useMatrixData';
import {usePartitionStepQuery} from './usePartitionStepQuery';

type PartitionStatus = OpJobPartitionStatusFragment;

export const OpJobPartitionsView: React.FC<{
  partitionSetName: string;
  repoAddress: RepoAddress;
}> = ({partitionSetName, repoAddress}) => {
  const repositorySelector = repoAddressToSelector(repoAddress);
  const queryResult = useQuery<PartitionsStatusQuery, PartitionsStatusQueryVariables>(
    PARTITIONS_STATUS_QUERY,
    {
      variables: {partitionSetName, repositorySelector},
    },
  );

  return (
    <Loading queryResult={queryResult}>
      {({partitionSetOrError}) => {
        if (
          partitionSetOrError.__typename !== 'PartitionSet' ||
          partitionSetOrError.partitionsOrError.__typename !== 'Partitions'
        ) {
          return null;
        }

        const partitionNames = partitionSetOrError.partitionsOrError.results.map(({name}) => name);

        return (
          <OpJobPartitionsViewContent
            partitionNames={partitionNames}
            partitionSet={partitionSetOrError}
            repoAddress={repoAddress}
          />
        );
      }}
    </Loading>
  );
};

export function usePartitionDurations(partitions: PartitionRuns[]) {
  return React.useMemo(() => {
    const stepDurationData: {[name: string]: {[key: string]: (number | undefined)[]}} = {};
    const runDurationData: {[name: string]: number | undefined} = {};

    partitions.forEach((p) => {
      if (!p.runsLoaded || p.runs.length === 0) {
        return;
      }
      const sortedRuns = p.runs.sort((a, b) => a.startTime || 0 - (b.startTime || 0));
      const lastRun = sortedRuns[sortedRuns.length - 1];
      stepDurationData[p.name] = {};
      runDurationData[p.name] =
        lastRun?.endTime && lastRun?.startTime ? lastRun.endTime - lastRun.startTime : undefined;

      lastRun.stepStats.forEach((s) => {
        stepDurationData[p.name][s.stepKey] = [
          s.endTime && s.startTime ? s.endTime - s.startTime : undefined,
        ];
      });
    });

    return {runDurationData, stepDurationData};
  }, [partitions]);
}

const OpJobPartitionsViewContent: React.FC<{
  partitionNames: string[];
  partitionSet: OpJobPartitionSetFragment;
  repoAddress: RepoAddress;
}> = ({partitionSet, partitionNames, repoAddress}) => {
  const {
    permissions: {canLaunchPartitionBackfill},
    disabledReasons,
  } = usePermissionsForLocation(repoAddress.location);
  const {viewport, containerProps} = useViewport();

  const [pageSize, setPageSize] = React.useState(60);
  const [offset, setOffset] = React.useState<number>(0);
  const [showSteps, setShowSteps] = React.useState(false);
  const [showBackfillSetup, setShowBackfillSetup] = React.useState(false);
  const [blockDialog, setBlockDialog] = React.useState(false);
  const repositorySelector = repoAddressToSelector(repoAddress);
  const [backfillRefetchCounter, setBackfillRefetchCounter] = React.useState(0);

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

  React.useEffect(() => {
    if (viewport.width && !showSteps) {
      // magical numbers to approximate the size of the window, which is calculated in the step
      // status component.  This approximation is to make sure that the window does not jump as
      // the pageSize gets recalculated
      const approxPageSize = getVisibleItemCount(viewport.width - GRID_FLOATING_CONTAINER_WIDTH);
      setPageSize(approxPageSize);
    }
  }, [viewport.width, showSteps, setPageSize]);

  const selectedPartitions = showSteps
    ? partitionNames.slice(
        Math.max(0, partitionNames.length - 1 - offset - pageSize),
        partitionNames.length - offset,
      )
    : partitionNames;

  const stepDurationData = usePartitionDurations(partitions).stepDurationData;

  const onSubmit = React.useCallback(() => setBlockDialog(true), []);

  const {runStatusData, runDurationData} = React.useMemo(() => {
    // Note: This view reads "run duration" from the `partitionStatusesOrError` GraphQL API,
    // rather than looking at the duration of the most recent run returned in `partitions` above
    // so that the latter can be loaded when you click "Show per-step status" only.
    const runStatusData: {[name: string]: RunStatus} = {};
    const runDurationData: {[name: string]: number | undefined} = {};

    (partitionSet.partitionStatusesOrError.__typename === 'PartitionStatuses'
      ? partitionSet.partitionStatusesOrError.results
      : []
    ).forEach((p) => {
      runStatusData[p.partitionName] = p.runStatus || RunStatus.NOT_STARTED;
      if (selectedPartitions.includes(p.partitionName)) {
        runDurationData[p.partitionName] = p.runDuration || undefined;
      }
    });
    return {runStatusData, runDurationData};
  }, [partitionSet, selectedPartitions]);

  const health = React.useMemo(() => {
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
        border={{width: 1, side: 'bottom', color: Colors.KeylineGray}}
        padding={{vertical: 16, horizontal: 24}}
      >
        <Subheading>Status</Subheading>
        <Box flex={{gap: 8}}>
          <Button onClick={() => setShowSteps(!showSteps)} active={showBackfillSetup}>
            {showSteps ? 'Hide per-step status' : 'Show per-step status'}
          </Button>
          {canLaunchPartitionBackfill ? (
            <Button
              onClick={() => setShowBackfillSetup(!showBackfillSetup)}
              icon={<Icon name="add_circle" />}
              active={showBackfillSetup}
            >
              Launch backfill...
            </Button>
          ) : (
            <Tooltip content={disabledReasons.canLaunchPartitionBackfill}>
              <Button icon={<Icon name="add_circle" />} disabled>
                Launch backfill...
              </Button>
            </Tooltip>
          )}
        </Box>
      </Box>
      <Box
        flex={{direction: 'row', alignItems: 'center'}}
        border={{width: 1, side: 'bottom', color: Colors.KeylineGray}}
        padding={{left: 8}}
      >
        <CountBox count={partitionNames.length} label="Total partitions" />
        <CountBox
          count={partitionNames.filter((x) => runStatusData[x] === RunStatus.FAILURE).length}
          label="Failed partitions"
        />
        <CountBox
          count={
            partitionNames.filter(
              (x) => !runStatusData[x] || runStatusData[x] === RunStatus.NOT_STARTED,
            ).length
          }
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
            onClick={(partitionName) => {
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
            }}
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
      <Box
        padding={{horizontal: 24, vertical: 16}}
        border={{side: 'horizontal', width: 1, color: Colors.KeylineGray}}
      >
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
        border={{side: 'horizontal', color: Colors.KeylineGray, width: 1}}
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
};

export const CountBox: React.FC<{
  count: number;
  label: string;
}> = ({count, label}) => (
  <Box padding={16} style={{flex: 1}} border={{side: 'right', width: 1, color: Colors.KeylineGray}}>
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
