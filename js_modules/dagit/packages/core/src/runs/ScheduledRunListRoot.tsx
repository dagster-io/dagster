import {useQuery} from '@apollo/client';
import {Page, Alert, ButtonLink, Colors, Group} from '@dagster-io/ui';
import * as React from 'react';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {graphql} from '../graphql';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {SchedulerInfo} from '../schedules/SchedulerInfo';
import {SchedulesNextTicks} from '../schedules/SchedulesNextTicks';
import {Loading} from '../ui/Loading';

import {RunsPageHeader} from './RunsPageHeader';

export const ScheduledRunListRoot = () => {
  useTrackPageView();
  useDocumentTitle('Scheduled runs');

  const queryResult = useQuery(SCHEDULER_INFO_QUERY, {
    fetchPolicy: 'cache-and-network',
    partialRefetch: true,
    notifyOnNetworkStatusChange: true,
  });

  const refreshState = useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  return (
    <Page>
      <RunsPageHeader refreshStates={[refreshState]} />
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
            <>
              <SchedulerInfo
                daemonHealth={instance.daemonHealth}
                padding={{vertical: 16, horizontal: 24}}
              />
              <SchedulesNextTicks repos={repositoriesOrError.nodes} />
            </>
          );
        }}
      </Loading>
    </Page>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default ScheduledRunListRoot;

const SCHEDULER_INFO_QUERY = graphql(`
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
`);
