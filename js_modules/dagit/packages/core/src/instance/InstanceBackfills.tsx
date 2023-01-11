import {useQuery} from '@apollo/client';
import {
  Alert,
  Box,
  CursorPaginationControls,
  NonIdealState,
  PageHeader,
  Heading,
  Page,
} from '@dagster-io/ui';
import * as React from 'react';

import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {graphql} from '../graphql';
import {
  InstanceBackfillsQueryQuery,
  InstanceBackfillsQueryQueryVariables,
} from '../graphql/graphql';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {OverviewTabs} from '../overview/OverviewTabs';
import {useCursorPaginatedQuery} from '../runs/useCursorPaginatedQuery';
import {Loading} from '../ui/Loading';

import {BackfillTable} from './BackfillTable';

const PAGE_SIZE = 10;

export const InstanceBackfills = () => {
  useTrackPageView();

  const queryData = useQuery(INSTANCE_HEALTH_FOR_BACKFILLS_QUERY);

  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    InstanceBackfillsQueryQuery,
    InstanceBackfillsQueryQueryVariables
  >({
    query: BACKFILLS_QUERY,
    variables: {},
    pageSize: PAGE_SIZE,
    nextCursorForResult: (result) =>
      result.partitionBackfillsOrError.__typename === 'PartitionBackfills'
        ? result.partitionBackfillsOrError.results[PAGE_SIZE - 1]?.backfillId
        : undefined,
    getResultArray: (result) =>
      result?.partitionBackfillsOrError.__typename === 'PartitionBackfills'
        ? result.partitionBackfillsOrError.results
        : [],
  });
  const refreshState = useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);
  useDocumentTitle('Backfills');

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
                  <Alert
                    intent="warning"
                    title="The backfill daemon is not running."
                    description={
                      <div>
                        See the{' '}
                        <a
                          href="https://docs.dagster.io/deployment/dagster-daemon"
                          target="_blank"
                          rel="noreferrer"
                        >
                          dagster-daemon documentation
                        </a>{' '}
                        for more information on how to deploy the dagster-daemon process.
                      </div>
                    }
                  />
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

const INSTANCE_HEALTH_FOR_BACKFILLS_QUERY = graphql(`
  query InstanceHealthForBackfillsQuery {
    instance {
      ...InstanceHealthFragment
    }
  }
`);

const BACKFILLS_QUERY = graphql(`
  query InstanceBackfillsQuery($cursor: String, $limit: Int) {
    partitionBackfillsOrError(cursor: $cursor, limit: $limit) {
      ... on PartitionBackfills {
        results {
          backfillId
          status
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
`);
