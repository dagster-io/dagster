import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {INSTANCE_HEALTH_FRAGMENT} from '../instance/InstanceHealthFragment';
import {REPOSITORY_SCHEDULES_FRAGMENT} from '../schedules/ScheduleUtils';
import {SchedulerInfo} from '../schedules/SchedulerInfo';
import {SchedulesNextTicks} from '../schedules/SchedulesNextTicks';
import {Alert} from '../ui/Alert';
import {Box} from '../ui/Box';
import {ButtonLink} from '../ui/ButtonLink';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {Loading} from '../ui/Loading';

import {SchedulerInfoQuery} from './types/SchedulerInfoQuery';
import {POLL_INTERVAL} from './useCursorPaginatedQuery';

export const AllScheduledTicks = () => {
  const queryResult = useQuery<SchedulerInfoQuery>(SCHEDULER_INFO_QUERY, {
    fetchPolicy: 'cache-and-network',
    pollInterval: POLL_INTERVAL,
    partialRefetch: true,
  });

  return (
    <Loading queryResult={queryResult}>
      {(result) => {
        const {repositoriesOrError, instance} = result;
        if (repositoriesOrError.__typename === 'PythonError') {
          const message = repositoriesOrError.message;
          return (
            <Alert
              intent="warning"
              title={
                <Group direction="row" spacing={4}>
                  <div>Could not load scheduled ticks.</div>
                  <ButtonLink
                    color={ColorsWIP.Link}
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
            <Box padding={{horizontal: 24}}>
              <SchedulerInfo daemonHealth={instance.daemonHealth} />
            </Box>
            <SchedulesNextTicks repos={repositoriesOrError.nodes} />
          </Group>
        );
      }}
    </Loading>
  );
};

const SCHEDULER_INFO_QUERY = gql`
  query SchedulerInfoQuery {
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
  ${INSTANCE_HEALTH_FRAGMENT}
  ${REPOSITORY_SCHEDULES_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
