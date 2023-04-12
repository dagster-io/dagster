import {gql, useQuery} from '@apollo/client';
import {
  Box,
  CursorPaginationControls,
  NonIdealState,
  PageHeader,
  Heading,
  Page,
} from '@dagster-io/ui';
import * as React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {OverviewTabs} from '../overview/OverviewTabs';
import {DaemonNotRunningAlertBody} from '../partitions/BackfillMessaging';
import {useCursorPaginatedQuery} from '../runs/useCursorPaginatedQuery';
import {Loading} from '../ui/Loading';

import {BackfillTable, BACKFILL_TABLE_FRAGMENT} from './BackfillTable';
import {INSTANCE_HEALTH_FRAGMENT} from './InstanceHealthFragment';
import {
  InstanceBackfillsQuery,
  InstanceBackfillsQueryVariables,
  InstanceHealthForBackfillsQuery,
  InstanceHealthForBackfillsQueryVariables,
} from './types/InstanceBackfills.types';

const PAGE_SIZE = 10;

export const InstanceBackfills = () => {
  useTrackPageView();
  useDocumentTitle('Overview | Backfills');

  const queryData = useQuery<
    InstanceHealthForBackfillsQuery,
    InstanceHealthForBackfillsQueryVariables
  >(INSTANCE_HEALTH_FOR_BACKFILLS_QUERY);

  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    InstanceBackfillsQuery,
    InstanceBackfillsQueryVariables
  >({
    query: BACKFILLS_QUERY,
    variables: {},
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

  return (
    <Page>
      <PageHeader
        title={<Heading>Overview</Heading>}
        tabs={<OverviewTabs tab="backfills" refreshState={refreshState} />}
      />
      <Loading queryResult={queryResult} allowStaleData={true}>
        {({partitionBackfillsOrError}) => {
          if (partitionBackfillsOrError.__typename === 'PythonError') {
            return <PythonErrorInfo error={partitionBackfillsOrError} />;
          }

          if (!partitionBackfillsOrError.results.length) {
            return (
              <Box padding={{vertical: 64}}>
                <NonIdealState
                  icon="no-results"
                  title="No backfills found"
                  description={<p>This instance does not have any backfill jobs.</p>}
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
                <div style={{marginTop: '16px'}}>
                  <CursorPaginationControls {...paginationProps} />
                </div>
              ) : null}
            </div>
          );
        }}
      </Loading>
    </Page>
  );
};

const INSTANCE_HEALTH_FOR_BACKFILLS_QUERY = gql`
  query InstanceHealthForBackfillsQuery {
    instance {
      ...InstanceHealthFragment
    }
  }

  ${INSTANCE_HEALTH_FRAGMENT}
`;

const BACKFILLS_QUERY = gql`
  query InstanceBackfillsQuery($cursor: String, $limit: Int) {
    partitionBackfillsOrError(cursor: $cursor, limit: $limit) {
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
