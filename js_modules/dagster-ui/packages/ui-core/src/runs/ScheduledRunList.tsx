import {Alert, ButtonLink, Colors, Group} from '@dagster-io/ui-components';

import {gql} from '../apollo-client';
import {ScheduledRunsListQuery} from './types/ScheduledRunList.types';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {INSTANCE_HEALTH_FRAGMENT} from '../instance/InstanceHealthFragment';
import {SchedulerInfo} from '../schedules/SchedulerInfo';
import {
  REPOSITORY_FOR_NEXT_TICKS_FRAGMENT,
  SchedulesNextTicks,
} from '../schedules/SchedulesNextTicks';

export const ScheduledRunList = ({result}: {result: ScheduledRunsListQuery}) => {
  const {repositoriesOrError, instance} = result;
  if (repositoriesOrError.__typename !== 'RepositoryConnection') {
    const message =
      repositoriesOrError.__typename === 'PythonError'
        ? repositoriesOrError.message
        : 'Repository not found';
    return (
      <Alert
        intent="warning"
        title={
          <Group direction="row" spacing={4}>
            <div>Could not load scheduled ticks.</div>
            <ButtonLink
              color={Colors.linkDefault()}
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
};

export const SCHEDULED_RUNS_LIST_QUERY = gql`
  query ScheduledRunsListQuery {
    instance {
      id
      ...InstanceHealthFragment
    }
    repositoriesOrError {
      ... on RepositoryConnection {
        nodes {
          id
          ... on Repository {
            id
            ...RepositoryForNextTicksFragment
          }
        }
      }
      ...PythonErrorFragment
    }
  }

  ${INSTANCE_HEALTH_FRAGMENT}
  ${REPOSITORY_FOR_NEXT_TICKS_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
