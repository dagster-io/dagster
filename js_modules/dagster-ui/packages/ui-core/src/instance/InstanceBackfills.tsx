import {
  Alert,
  Box,
  Colors,
  CursorPaginationControls,
  NonIdealState,
  Spinner,
} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import {gql} from '../apollo-client';
import {BACKFILL_TABLE_FRAGMENT, BackfillTable} from './backfill/BackfillTable';
import {useBulkActionStatusFilter} from './useBulkActionStatusFilter';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {
  InstanceBackfillsQuery,
  InstanceBackfillsQueryVariables,
} from './types/InstanceBackfills.types';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {BulkActionStatus} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {DaemonNotRunningAlert, useIsBackfillDaemonHealthy} from '../partitions/BackfillMessaging';
import {useCursorPaginatedQuery} from '../runs/useCursorPaginatedQuery';
import {useFilters} from '../ui/BaseFilters';

const PAGE_SIZE = 10;

export const InstanceBackfills = () => {
  useTrackPageView();
  useDocumentTitle('Overview | Backfills');

  const [statusState, setStatusState] = useQueryPersistedState<Set<BulkActionStatus>>({
    encode: (vals) => ({status: vals.size ? Array.from(vals).join(',') : undefined}),
    decode: (qs) => new Set((qs.status?.split(',') as BulkActionStatus[]) || []),
  });

  const statusFilter = useBulkActionStatusFilter(statusState, setStatusState);
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

  const isDaemonHealthy = useIsBackfillDaemonHealthy();
  const refreshState = useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);
  const {loading, data} = queryResult;
  const [didDismissBackfillPageAlert, setDidDismissBackfillPageAlert] =
    useStateWithStorage<boolean>('new_backfill_location_alert', (json) => !!json);

  interface AlertProps {
    setDidDismissBackfillPageAlert: (didDismissBackfillPageAlert: boolean) => void;
  }

  const BackfillPageDeprecationAlert = (props: AlertProps) => {
    const {setDidDismissBackfillPageAlert} = props;

    return (
      <Box padding={8} border="top-and-bottom">
        <Alert
          title={
            <>
              <span>Backfills are moving:</span>
              <span style={{fontWeight: 'normal'}}>
                {' '}
                We&apos;re incorporating backfills into the <Link to="/runs/">Runs</Link> page to
                unify the UI and provide one page to see all of your executions. The Backfills page
                will be removed in a future release.{' '}
                <a
                  href="https://github.com/dagster-io/dagster/discussions/24898"
                  target="_blank"
                  rel="noreferrer"
                >
                  Share feedback
                </a>{' '}
              </span>
            </>
          }
          onClose={() => setDidDismissBackfillPageAlert(true)}
        />
      </Box>
    );
  };

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

    return (
      <div>
        {isDaemonHealthy ? null : (
          <Box padding={{horizontal: 24, bottom: 16}}>
            <DaemonNotRunningAlert />
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
      {!didDismissBackfillPageAlert ? (
        <BackfillPageDeprecationAlert
          setDidDismissBackfillPageAlert={setDidDismissBackfillPageAlert}
        />
      ) : null}
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
