import {gql, useQuery} from '@apollo/client';
import {Callout, Colors} from '@blueprintjs/core';
import * as React from 'react';

import {showCustomAlert} from 'src/app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from 'src/app/PythonErrorInfo';
import {INSTANCE_HEALTH_FRAGMENT} from 'src/instance/InstanceHealthFragment';
import {ScheduledTicksFragment} from 'src/runs/types/ScheduledTicksFragment';
import {SchedulerInfoQuery} from 'src/runs/types/SchedulerInfoQuery';
import {REPOSITORY_SCHEDULES_FRAGMENT} from 'src/schedules/ScheduleUtils';
import {SchedulerInfo, SCHEDULER_FRAGMENT} from 'src/schedules/SchedulerInfo';
import {SchedulesNextTicks} from 'src/schedules/SchedulesNextTicks';
import {ButtonLink} from 'src/ui/ButtonLink';
import {Group} from 'src/ui/Group';

export const AllScheduledTicks: React.FC<{repos: ScheduledTicksFragment}> = ({repos}) => {
  const {data} = useQuery<SchedulerInfoQuery>(SCHEDULER_INFO_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  const content = () => {
    if (repos.__typename === 'PythonError') {
      const message = repos.message;
      return (
        <Callout intent="warning">
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
        </Callout>
      );
    }

    return <SchedulesNextTicks repos={repos.nodes} />;
  };

  return (
    <Group direction="column" spacing={16}>
      {data ? (
        <SchedulerInfo
          schedulerOrError={data.scheduler}
          daemonHealth={data.instance.daemonHealth}
        />
      ) : null}
      {content()}
    </Group>
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
  }
  ${SCHEDULER_FRAGMENT}
  ${INSTANCE_HEALTH_FRAGMENT}
`;

export const SCHEDULED_TICKS_FRAGMENT = gql`
  fragment ScheduledTicksFragment on RepositoriesOrError {
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
  ${REPOSITORY_SCHEDULES_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
