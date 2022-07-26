import {gql, useQuery} from '@apollo/client';
import {
  Box,
  Button,
  Dialog,
  Icon,
  Tooltip,
  Colors,
  CursorPaginationControls,
  CursorPaginationProps,
  NonIdealState,
} from '@dagster-io/ui';
import * as React from 'react';

import {usePermissions} from '../app/Permissions';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {OptionsContainer} from '../gantt/VizComponents';
import {useViewport} from '../gantt/useViewport';
import {BackfillTable, BACKFILL_TABLE_FRAGMENT} from '../instance/BackfillTable';
import {RepositorySelector, RunStatus} from '../types/globalTypes';
import {Loading} from '../ui/Loading';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {BackfillPartitionSelector} from './BackfillSelector';
import {PartitionGraph} from './PartitionGraph';
import {PartitionStatus} from './PartitionStatus';
import {PartitionStepStatus} from './PartitionStepStatus';
import {
  PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PartitionStatuses_results,
  PartitionsStatusQuery_partitionSetOrError_PartitionSet,
  PartitionsStatusQuery,
  PartitionsStatusQueryVariables,
} from './types/PartitionsStatusQuery';
import {PipelinePartitionsRootQuery_partitionSetsOrError_PartitionSets_results} from './types/PipelinePartitionsRootQuery';
import {usePartitionStepQuery} from './usePartitionStepQuery';

type PartitionSet = PipelinePartitionsRootQuery_partitionSetsOrError_PartitionSets_results;
type PartitionStatus = PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PartitionStatuses_results;

const FAILED_STATUSES = [RunStatus.FAILURE, RunStatus.CANCELED, RunStatus.CANCELING];

export const PartitionView: React.FC<{
  partitionSet: PartitionSet;
  repoAddress: RepoAddress;
}> = ({partitionSet, repoAddress}) => {
  const repositorySelector = repoAddressToSelector(repoAddress);
  const queryResult = useQuery<PartitionsStatusQuery, PartitionsStatusQueryVariables>(
    PARTITIONS_STATUS_QUERY,
    {
      variables: {
        partitionSetName: partitionSet.name,
        repositorySelector,
      },
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
          <PartitionViewContent
            partitionNames={partitionNames}
            partitionSet={partitionSetOrError}
            repoAddress={repoAddress}
          />
        );
      }}
    </Loading>
  );
};

const PartitionViewContent: React.FC<{
  partitionNames: string[];
  partitionSet: PartitionsStatusQuery_partitionSetOrError_PartitionSet;
  repoAddress: RepoAddress;
}> = ({partitionSet, partitionNames, repoAddress}) => {
  const [pageSize, setPageSize] = React.useState(60);
  const [offset, setOffset] = React.useState<number>(0);
  const [showSteps, setShowSteps] = React.useState(false);
  const [showBackfillSetup, setShowBackfillSetup] = React.useState(false);
  const [blockDialog, setBlockDialog] = React.useState(false);
  const repositorySelector = repoAddressToSelector(repoAddress);
  const {canLaunchPartitionBackfill} = usePermissions();
  const {viewport, containerProps} = useViewport();
  const [backfillRefetchCounter, setBackfillRefetchCounter] = React.useState(0);
  const partitions = usePartitionStepQuery(
    partitionSet.name,
    partitionNames,
    pageSize,
    [],
    partitionSet.pipelineName,
    offset,
    !showSteps,
  );

  React.useEffect(() => {
    if (viewport.width && !showSteps) {
      // magical numbers to approximate the size of the window, which is calculated in the step
      // status component.  This approximation is to make sure that the window does not jump as
      // the pageSize gets recalculated
      const _approximatePageSize = Math.ceil((viewport.width - 330) / 32) - 3;
      setPageSize(_approximatePageSize);
    }
  }, [viewport.width, showSteps, setPageSize]);

  const selectedPartitions = showSteps
    ? partitionNames.slice(
        Math.max(0, partitionNames.length - 1 - offset - pageSize),
        partitionNames.length - offset,
      )
    : partitionNames;

  const runDurationData: {[name: string]: number | undefined} = {};

  const stepDurationData: {[name: string]: {[key: string]: (number | undefined)[]}} = {};
  partitions.forEach((p) => {
    if (!p.runsLoaded || p.runs.length === 0) {
      return;
    }
    const lastRun = p.runs[p.runs.length - 1];
    stepDurationData[p.name] = {};
    lastRun.stepStats.forEach((s) => {
      stepDurationData[p.name][s.stepKey] = [
        s.endTime && s.startTime ? s.endTime - s.startTime : undefined,
      ];
    });
  });
  const statusData: {[name: string]: RunStatus | null} = {};
  (partitionSet.partitionStatusesOrError.__typename === 'PartitionStatuses'
    ? partitionSet.partitionStatusesOrError.results
    : []
  ).forEach((p) => {
    statusData[p.partitionName] = p.runStatus;
    if (selectedPartitions.includes(p.partitionName)) {
      runDurationData[p.partitionName] = p.runDuration || undefined;
    }
  });

  const onSubmit = React.useCallback(() => setBlockDialog(true), []);

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
            partitionData={statusData}
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
        padding={16}
      >
        <div>
          <strong>Status</strong>
        </div>
        <Box flex={{gap: 8}}>
          <Button onClick={() => setShowSteps(!showSteps)} active={showBackfillSetup}>
            {showSteps ? 'Hide per-step status' : 'Show per-step status'}
          </Button>
          {canLaunchPartitionBackfill.enabled ? (
            <Button
              onClick={() => setShowBackfillSetup(!showBackfillSetup)}
              icon={<Icon name="add_circle" />}
              active={showBackfillSetup}
            >
              Launch backfill...
            </Button>
          ) : (
            <Tooltip content={canLaunchPartitionBackfill.disabledReason}>
              <Button icon={<Icon name="add_circle" />} disabled>
                Launch backfill...
              </Button>
            </Tooltip>
          )}
        </Box>
      </Box>
      <Box
        flex={{justifyContent: 'space-between', direction: 'row', alignItems: 'center'}}
        border={{width: 1, side: 'bottom', color: Colors.KeylineGray}}
      >
        <CountBox count={partitionNames.length} label="Total partitions" />
        <CountBox
          count={
            partitionNames.filter((x) => {
              const status = statusData[x];
              return status && FAILED_STATUSES.includes(status);
            }).length
          }
          label="Failed partitions"
        />
        <CountBox
          count={partitionNames.filter((x) => !statusData[x]).length}
          label="Missing partitions"
        />
      </Box>
      <Box margin={16}>
        <div {...containerProps}>
          <PartitionStatus
            partitionNames={partitionNames}
            partitionData={statusData}
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
            <PartitionStepStatus
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
      <OptionsContainer>
        <strong>Run duration</strong>
      </OptionsContainer>
      <Box margin={24}>
        <PartitionGraph
          isJob={true}
          title="Execution Time by Partition"
          yLabel="Execution time (secs)"
          partitionNames={showSteps ? selectedPartitions : partitionNames}
          jobDataByPartition={runDurationData}
        />
      </Box>
      {showSteps ? (
        <>
          <OptionsContainer>
            <strong>Step duration</strong>
          </OptionsContainer>
          <Box margin={24}>
            <PartitionGraph
              isJob={true}
              title="Execution Time by Partition"
              yLabel="Execution time (secs)"
              partitionNames={selectedPartitions}
              stepDataByPartition={stepDurationData}
            />
          </Box>
        </>
      ) : null}
      <OptionsContainer>
        <strong>Backfill History</strong>
      </OptionsContainer>
      <Box margin={16}>
        <JobBackfills
          partitionSet={partitionSet}
          repositorySelector={repositorySelector}
          partitionNames={partitionNames}
          refetchCounter={backfillRefetchCounter}
        />
      </Box>
    </div>
  );
};

const BACKFILL_PAGE_SIZE = 10;

const JobBackfills = ({
  partitionSet,
  partitionNames,
  repositorySelector,
  refetchCounter,
}: {
  partitionSet: PartitionsStatusQuery_partitionSetOrError_PartitionSet;
  partitionNames: string[];
  repositorySelector: RepositorySelector;
  refetchCounter: number;
}) => {
  const [cursorStack, setCursorStack] = React.useState<string[]>(() => []);
  const [cursor, setCursor] = React.useState<string | undefined>();
  const queryResult = useQuery(JOB_BACKFILLS_QUERY, {
    variables: {
      partitionSetName: partitionSet.name,
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
          return <NonIdealState title={`No backfills for ${pipelineName}`} icon="no-results" />;
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
              showPartitionSet={false}
              allPartitions={partitionNames}
            />
            <CursorPaginationControls {...paginationProps} />
          </>
        );
      }}
    </Loading>
  );
};

const CountBox: React.FC<{
  count: number;
  label: string;
}> = ({count, label}) => (
  <div style={{flex: 1, borderLeft: `1px solid ${Colors.KeylineGray}`, padding: 16}}>
    <div style={{fontSize: 18, marginBottom: 4}}>
      <strong>{count}</strong>
    </div>
    <div>{label}</div>
  </div>
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
          __typename
          ... on PartitionStatuses {
            results {
              id
              partitionName
              runStatus
              runDuration
            }
          }
          ...PythonErrorFragment
        }
      }
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

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
