import {gql, useQuery} from '@apollo/client';
import {Page, PageHeader, Heading, Alert, ButtonLink, Colors, Group} from '@dagster-io/ui';
import * as React from 'react';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {INSTANCE_HEALTH_FRAGMENT} from '../instance/InstanceHealthFragment';
import {REPOSITORY_SCHEDULES_FRAGMENT} from '../schedules/ScheduleUtils';
import {SchedulerInfo} from '../schedules/SchedulerInfo';
import {SchedulesNextTicks} from '../schedules/SchedulesNextTicks';
import {Loading} from '../ui/Loading';

import {RunListTabs} from './RunListTabs';
import {SchedulerInfoQuery} from './types/SchedulerInfoQuery';

export const ScheduledRunListRoot = () => {
  useTrackPageView();
  useDocumentTitle('Scheduled runs');

  const queryResult = useQuery<SchedulerInfoQuery>(SCHEDULER_INFO_QUERY, {
    fetchPolicy: 'cache-and-network',
    partialRefetch: true,
    notifyOnNetworkStatusChange: true,
  });

  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  return (
    <Page>
      <PageHeader title={<Heading>Runs</Heading>} tabs={<RunListTabs />} />
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
            <Group direction="column" spacing={24}>
              <SchedulerInfo daemonHealth={instance.daemonHealth} />
              <SchedulesNextTicks repos={repositoriesOrError.nodes} />
            </Group>
          );
        }}
      </Loading>
    </Page>
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
