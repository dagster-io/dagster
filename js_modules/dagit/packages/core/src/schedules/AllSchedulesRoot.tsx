import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {QueryCountdown} from '../app/QueryCountdown';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {INSTANCE_HEALTH_FRAGMENT} from '../instance/InstanceHealthFragment';
import {JOB_STATE_FRAGMENT} from '../jobs/JobUtils';
import {JobType} from '../types/globalTypes';
import {Group} from '../ui/Group';
import {Loading} from '../ui/Loading';
import {Page} from '../ui/Page';
import {PageHeader} from '../ui/PageHeader';
import {Heading} from '../ui/Text';

import {AllSchedules} from './AllSchedules';
import {SCHEDULE_FRAGMENT} from './ScheduleUtils';
import {SCHEDULER_FRAGMENT} from './SchedulerInfo';
import {AllSchedulesQuery} from './types/AllSchedulesQuery';

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

const ALL_SCHEDULES_QUERY = gql`
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
