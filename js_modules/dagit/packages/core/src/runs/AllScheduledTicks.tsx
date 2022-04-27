import {gql, useQuery} from '@apollo/client';
import {Alert, Box, ButtonLink, Colors, Group} from '@dagster-io/ui';
import * as React from 'react';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {INSTANCE_HEALTH_FRAGMENT} from '../instance/InstanceHealthFragment';
import {REPOSITORY_SCHEDULES_FRAGMENT} from '../schedules/ScheduleUtils';
import {SchedulerInfo} from '../schedules/SchedulerInfo';
import {SchedulesNextTicks} from '../schedules/SchedulesNextTicks';
import {Loading} from '../ui/Loading';

import {SchedulerInfoQuery} from './types/SchedulerInfoQuery';

export const AllScheduledTicks = () => {
  const queryResult = useQuery<SchedulerInfoQuery>(SCHEDULER_INFO_QUERY, {
    fetchPolicy: 'cache-and-network',
    partialRefetch: true,
    notifyOnNetworkStatusChange: true,
  });

  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

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
                    color={Colors.Link}
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
          <div>
            <Box
              padding={{horizontal: 24, vertical: 16}}
              border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
            >
              <SchedulerInfo daemonHealth={instance.daemonHealth} />
            </Box>
            <SchedulesNextTicks repos={repositoriesOrError.nodes} />
          </div>
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
