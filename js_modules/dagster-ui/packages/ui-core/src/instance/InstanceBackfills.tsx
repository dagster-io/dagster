import {gql, useQuery} from '@apollo/client';
import {
  Box,
  Colors,
  CursorPaginationControls,
  NonIdealState,
  Spinner,
} from '@dagster-io/ui-components';

import {INSTANCE_HEALTH_FRAGMENT} from './InstanceHealthFragment';
import {BACKFILL_TABLE_FRAGMENT, BackfillTable} from './backfill/BackfillTable';
import {
  InstanceBackfillsQuery,
  InstanceBackfillsQueryVariables,
  InstanceHealthForBackfillsQuery,
  InstanceHealthForBackfillsQueryVariables,
} from './types/InstanceBackfills.types';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {BulkActionStatus} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {DaemonNotRunningAlertBody} from '../partitions/BackfillMessaging';
import {useCursorPaginatedQuery} from '../runs/useCursorPaginatedQuery';
import {useFilters} from '../ui/Filters';
import {useStaticSetFilter} from '../ui/Filters/useStaticSetFilter';

const PAGE_SIZE = 10;

const labelForBackfillStatus = (key: BulkActionStatus) => {
  switch (key) {
    case BulkActionStatus.CANCELED:
      return 'Canceled';
    case BulkActionStatus.CANCELING:
      return 'Canceling';
    case BulkActionStatus.COMPLETED:
      return 'Completed';
    case BulkActionStatus.FAILED:
      return 'Failed';
    case BulkActionStatus.REQUESTED:
      return 'In progress';
  }
};

const backfillStatusValues = Object.keys(BulkActionStatus).map((key) => {
  const status = key as BulkActionStatus;
  const label = labelForBackfillStatus(status);
  return {
    label,
    value: status,
    match: [status, label],
  };
});

export const InstanceBackfills = () => {
  useTrackPageView();
  useDocumentTitle('Overview | Backfills');

  const queryData = useQuery<
    InstanceHealthForBackfillsQuery,
    InstanceHealthForBackfillsQueryVariables
  >(INSTANCE_HEALTH_FOR_BACKFILLS_QUERY);

  const statusFilter = useStaticSetFilter<BulkActionStatus>({
    name: 'Status',
    icon: 'status',
    allValues: backfillStatusValues,
    allowMultipleSelections: false,
    closeOnSelect: true,
    renderLabel: ({value}) => <div>{labelForBackfillStatus(value)}</div>,
    getStringValue: (status) => labelForBackfillStatus(status),
  });

  const {state: statusState} = statusFilter;

  const {button, activeFiltersJsx} = useFilters({filters: [statusFilter]});

  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    InstanceBackfillsQuery,
    InstanceBackfillsQueryVariables
  >({
    query: BACKFILLS_QUERY,
    variables: {
      status: statusState.size > 0 ? Array.from(statusState)[0]! : undefined,
    },
    pageSize: PAGE_SIZE,
    nextCursorForResult: (result) =>
      result.partitionBackfillsOrError.__typename === 'PartitionBackfills'
        ? result.partitionBackfillsOrError.results[PAGE_SIZE - 1]?.id
        : undefined,
    getResultArray: (result) =>
      result?.partitionBackfillsOrError.__typename === 'PartitionBackfills'
        ? result.partitionBackfillsOrError.results
        : [],
  });

  const refreshState = useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);
  const {loading, data} = queryResult;

  const content = () => {
    if (loading && !data) {
      return (
        <Box padding={{vertical: 64}} flex={{direction: 'column', alignItems: 'center'}}>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
            <Spinner purpose="body-text" />
            <div style={{color: Colors.textLight()}}>Loading backfills…</div>
          </Box>
        </Box>
      );
    }

    const partitionBackfillsOrError = data?.partitionBackfillsOrError;
    if (partitionBackfillsOrError?.__typename === 'PythonError') {
      return <PythonErrorInfo error={partitionBackfillsOrError} />;
    }

    if (!partitionBackfillsOrError || !partitionBackfillsOrError?.results.length) {
      if (statusState.size > 0) {
        return (
          <Box padding={{vertical: 64}}>
            <NonIdealState
              icon="no-results"
              title="No matching backfills"
              description="No backfills were found for this filter."
            />
          </Box>
        );
      }

      return (
        <Box padding={{vertical: 64}}>
          <NonIdealState
            icon="no-results"
            title="No backfills found"
            description="This instance does not have any backfill jobs."
          />
        </Box>
      );
    }

    const daemonHealths = queryData.data?.instance.daemonHealth.allDaemonStatuses || [];
    const backfillHealths = daemonHealths
      .filter((daemon) => daemon.daemonType === 'BACKFILL')
      .map((daemon) => daemon.required && daemon.healthy);
    const isBackfillHealthy = backfillHealths.length && backfillHealths.every((x) => x);

    return (
      <div>
        {isBackfillHealthy ? null : (
          <Box padding={{horizontal: 24, vertical: 16}}>
            <DaemonNotRunningAlertBody />
          </Box>
        )}
        <BackfillTable
          backfills={partitionBackfillsOrError.results.slice(0, PAGE_SIZE)}
          refetch={queryResult.refetch}
        />
        {partitionBackfillsOrError.results.length > 0 ? (
          <Box margin={{top: 16}}>
            <CursorPaginationControls {...paginationProps} />
          </Box>
        ) : null}
      </div>
    );
  };

  return (
    <>
      <Box
        padding={{vertical: 12, horizontal: 20}}
        flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
      >
        <Box flex={{direction: 'column', gap: 8}}>
          <div>{button}</div>
          {activeFiltersJsx}
        </Box>
        <QueryRefreshCountdown refreshState={refreshState} />
      </Box>
      {content()}
    </>
  );
};

const INSTANCE_HEALTH_FOR_BACKFILLS_QUERY = gql`
  query InstanceHealthForBackfillsQuery {
    instance {
      id
      ...InstanceHealthFragment
    }
  }

  ${INSTANCE_HEALTH_FRAGMENT}
`;

const BACKFILLS_QUERY = gql`
  query InstanceBackfillsQuery($status: BulkActionStatus, $cursor: String, $limit: Int) {
    partitionBackfillsOrError(status: $status, cursor: $cursor, limit: $limit) {
      ... on PartitionBackfills {
        results {
          id
          status
          isValidSerialization
          numPartitions
          timestamp
          partitionSetName
          partitionSet {
            id
            name
            mode
            pipelineName
            repositoryOrigin {
              id
              repositoryName
              repositoryLocationName
            }
          }
          error {
            ...PythonErrorFragment
          }

          ...BackfillTableFragment
        }
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
  ${BACKFILL_TABLE_FRAGMENT}
`;
