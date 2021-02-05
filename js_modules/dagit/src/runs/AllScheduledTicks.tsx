import {gql, useQuery} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import * as React from 'react';

import {showCustomAlert} from 'src/app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from 'src/app/PythonErrorInfo';
import {INSTANCE_HEALTH_FRAGMENT} from 'src/instance/InstanceHealthFragment';
import {SchedulerInfoQuery} from 'src/runs/types/SchedulerInfoQuery';
import {POLL_INTERVAL} from 'src/runs/useCursorPaginatedQuery';
import {REPOSITORY_SCHEDULES_FRAGMENT} from 'src/schedules/ScheduleUtils';
import {SchedulerInfo, SCHEDULER_FRAGMENT} from 'src/schedules/SchedulerInfo';
import {SchedulesNextTicks} from 'src/schedules/SchedulesNextTicks';
import {Alert} from 'src/ui/Alert';
import {ButtonLink} from 'src/ui/ButtonLink';
import {Group} from 'src/ui/Group';
import {Loading} from 'src/ui/Loading';

export const AllScheduledTicks = () => {
  const queryResult = useQuery<SchedulerInfoQuery>(SCHEDULER_INFO_QUERY, {
    fetchPolicy: 'cache-and-network',
    pollInterval: POLL_INTERVAL,
    partialRefetch: true,
  });

  return (
    <Loading queryResult={queryResult}>
      {(result) => {
        const {repositoriesOrError, instance, scheduler} = result;
        if (repositoriesOrError.__typename === 'PythonError') {
          const message = repositoriesOrError.message;
          return (
            <Alert
              intent="warning"
              title={
                <Group direction="row" spacing={4}>
                  <div>Could not load scheduled ticks.</div>
                  <ButtonLink
                    color={Colors.BLUE3}
                    underline="always"
                    onClick={() => {
                      showCustomAlert({
                        title: 'Python error',
                        body: message,
                      });
                    }}
                  >
                    View error
                  </ButtonLink>
                </Group>
              }
            />
          );
        }
        return (
          <Group direction="column" spacing={16}>
            <SchedulerInfo schedulerOrError={scheduler} daemonHealth={instance.daemonHealth} />
            <SchedulesNextTicks repos={repositoriesOrError.nodes} />
          </Group>
        );
      }}
    </Loading>
  );
};

const SCHEDULER_INFO_QUERY = gql`
  query SchedulerInfoQuery {
    scheduler {
      ...SchedulerFragment
    }
    instance {
      ...InstanceHealthFragment
    }
    repositoriesOrError {
      ... on RepositoryConnection {
        nodes {
          __typename
          id
          ... on Repository {
            ...RepositorySchedulesFragment
          }
        }
      }
      ...PythonErrorFragment
    }
  }
  ${SCHEDULER_FRAGMENT}
  ${INSTANCE_HEALTH_FRAGMENT}
  ${REPOSITORY_SCHEDULES_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
