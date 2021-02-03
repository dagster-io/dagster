import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {PYTHON_ERROR_FRAGMENT} from 'src/app/PythonErrorInfo';
import {QueryCountdown} from 'src/app/QueryCountdown';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {INSTANCE_HEALTH_FRAGMENT} from 'src/instance/InstanceHealthFragment';
import {JOB_STATE_FRAGMENT} from 'src/jobs/JobUtils';
import {AllSchedules} from 'src/schedules/AllSchedules';
import {SCHEDULE_FRAGMENT} from 'src/schedules/ScheduleUtils';
import {SCHEDULER_FRAGMENT} from 'src/schedules/SchedulerInfo';
import {AllSchedulesQuery} from 'src/schedules/types/AllSchedulesQuery';
import {JobType} from 'src/types/globalTypes';
import {Group} from 'src/ui/Group';
import {Loading} from 'src/ui/Loading';
import {Page} from 'src/ui/Page';
import {PageHeader} from 'src/ui/PageHeader';
import {Heading} from 'src/ui/Text';

const POLL_INTERVAL = 15 * 1000;

export const AllSchedulesRoot = () => {
  useDocumentTitle('Schedules');

  const queryResult = useQuery<AllSchedulesQuery>(ALL_SCHEDULES_QUERY, {
    fetchPolicy: 'cache-and-network',
    pollInterval: POLL_INTERVAL,
    partialRefetch: true,
    notifyOnNetworkStatusChange: true,
    variables: {
      jobType: JobType.SCHEDULE,
    },
  });

  return (
    <Page>
      <Group direction="column" spacing={16}>
        <PageHeader
          title={<Heading>Schedules</Heading>}
          right={<QueryCountdown pollInterval={POLL_INTERVAL} queryResult={queryResult} />}
        />
        <Loading allowStaleData queryResult={queryResult}>
          {(data) => <AllSchedules {...data} />}
        </Loading>
      </Group>
    </Page>
  );
};

const REPOSITORIES_FRAGMENT = gql`
  fragment AllSchedulesRepositoriesFragment on RepositoriesOrError {
    ... on RepositoryConnection {
      nodes {
        id
        name
        location {
          id
          name
        }
        schedules {
          id
          ...ScheduleFragment
        }
      }
    }
    ...PythonErrorFragment
  }

  ${SCHEDULE_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

const UNLOADABLES_FRAGMENT = gql`
  fragment AllSchedulesUnloadablesFragment on JobStatesOrError {
    ... on JobStates {
      results {
        id
        ...JobStateFragment
      }
    }
    ...PythonErrorFragment
  }

  ${JOB_STATE_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

export const ALL_SCHEDULES_QUERY = gql`
  query AllSchedulesQuery($jobType: JobType) {
    repositoriesOrError {
      ...AllSchedulesRepositoriesFragment
    }
    instance {
      ...InstanceHealthFragment
    }
    scheduler {
      ...SchedulerFragment
    }
    unloadableJobStatesOrError(jobType: $jobType) {
      ...AllSchedulesUnloadablesFragment
    }
  }

  ${REPOSITORIES_FRAGMENT}
  ${INSTANCE_HEALTH_FRAGMENT}
  ${SCHEDULER_FRAGMENT}
  ${UNLOADABLES_FRAGMENT}
`;
