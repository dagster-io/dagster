import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {INSTIGATION_STATE_FRAGMENT} from '../instigation/InstigationUtils';
import {UnloadableSchedules} from '../instigation/Unloadable';
import {SCHEDULE_FRAGMENT} from '../schedules/ScheduleUtils';
import {SchedulerInfo} from '../schedules/SchedulerInfo';
import {SchedulesTable} from '../schedules/SchedulesTable';
import {InstigationType} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {Loading} from '../ui/Loading';
import {NonIdealState} from '../ui/NonIdealState';
import {PageHeader} from '../ui/PageHeader';
import {Heading, Subheading} from '../ui/Text';
import {REPOSITORY_INFO_FRAGMENT} from '../workspace/RepositoryInformation';
import {buildRepoPath, buildRepoAddress} from '../workspace/buildRepoAddress';

import {INSTANCE_HEALTH_FRAGMENT} from './InstanceHealthFragment';
import {InstanceTabs} from './InstanceTabs';
import {InstanceSchedulesQuery} from './types/InstanceSchedulesQuery';

const POLL_INTERVAL = 15000;

export const InstanceSchedules = React.memo(() => {
  const queryData = useQuery<InstanceSchedulesQuery>(INSTANCE_SCHEDULES_QUERY, {
    fetchPolicy: 'cache-and-network',
    pollInterval: POLL_INTERVAL,
    notifyOnNetworkStatusChange: true,
  });

  return (
    <>
      <PageHeader
        title={<Heading>Instance status</Heading>}
        tabs={<InstanceTabs tab="schedules" queryData={queryData} />}
      />
      <Loading queryResult={queryData} allowStaleData={true}>
        {(data) => <AllSchedules data={data} />}
      </Loading>
    </>
  );
});

const AllSchedules: React.FC<{data: InstanceSchedulesQuery}> = ({data}) => {
  const {instance, repositoriesOrError, unloadableInstigationStatesOrError} = data;

  if (repositoriesOrError.__typename === 'PythonError') {
    return <PythonErrorInfo error={repositoriesOrError} />;
  }
  if (unloadableInstigationStatesOrError.__typename === 'PythonError') {
    return <PythonErrorInfo error={unloadableInstigationStatesOrError} />;
  }

  const unloadable = unloadableInstigationStatesOrError.results;
  const withSchedules = repositoriesOrError.nodes.filter(
    (repository) => repository.schedules.length,
  );

  const loadedSchedulesSection = withSchedules.length ? (
    <>
      <Box padding={{vertical: 16, horizontal: 24}}>
        <SchedulerInfo daemonHealth={instance.daemonHealth} />
      </Box>
      {withSchedules.map((repository) => (
        <React.Fragment key={repository.name}>
          <Box
            padding={{vertical: 16, horizontal: 24}}
            border={{side: 'top', width: 1, color: ColorsWIP.KeylineGray}}
          >
            <Subheading>{`${buildRepoPath(repository.name, repository.location.name)}`}</Subheading>
          </Box>
          <Box padding={{bottom: 16}}>
            <SchedulesTable
              repoAddress={buildRepoAddress(repository.name, repository.location.name)}
              schedules={repository.schedules}
            />
          </Box>
        </React.Fragment>
      ))}
    </>
  ) : null;

  const unloadableSchedules = unloadable.filter(
    (state) => state.instigationType === InstigationType.SCHEDULE,
  );

  const unloadableSchedulesSection = unloadableSchedules.length ? (
    <UnloadableSchedules scheduleStates={unloadableSchedules} />
  ) : null;

  if (!loadedSchedulesSection && !unloadableSchedulesSection) {
    return (
      <Box margin={{top: 32}}>
        <NonIdealState
          icon="schedule"
          title="No schedules found"
          description={
            <div>
              This instance does not have any schedules defined. Visit the{' '}
              <a
                href="https://docs.dagster.io/concepts/partitions-schedules-sensors/schedules"
                target="_blank"
                rel="noreferrer"
              >
                scheduler documentation
              </a>{' '}
              for more information about scheduling runs in Dagster.
            </div>
          }
        />
      </Box>
    );
  }

  return (
    <Group direction="column" spacing={32}>
      {loadedSchedulesSection}
      {unloadableSchedulesSection}
    </Group>
  );
};

const INSTANCE_SCHEDULES_QUERY = gql`
  query InstanceSchedulesQuery {
    instance {
      ...InstanceHealthFragment
    }
    repositoriesOrError {
      __typename
      ... on RepositoryConnection {
        nodes {
          id
          name
          ...RepositoryInfoFragment
          schedules {
            id
            ...ScheduleFragment
          }
        }
      }
      ...PythonErrorFragment
    }
    unloadableInstigationStatesOrError {
      ... on InstigationStates {
        results {
          id
          ...InstigationStateFragment
        }
      }
      ...PythonErrorFragment
    }
  }

  ${INSTANCE_HEALTH_FRAGMENT}
  ${REPOSITORY_INFO_FRAGMENT}
  ${SCHEDULE_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
  ${INSTIGATION_STATE_FRAGMENT}
`;
