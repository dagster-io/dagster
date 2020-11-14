import {gql, useQuery} from '@apollo/client';
import {Colors, IBreadcrumbProps, NonIdealState} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import React from 'react';

import {ScrollContainer} from 'src/ListComponents';
import {Loading} from 'src/Loading';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {TopNav} from 'src/nav/TopNav';
import {
  REPOSITORY_SCHEDULES_FRAGMENT,
  SCHEDULE_DEFINITION_FRAGMENT,
  SCHEDULE_STATE_FRAGMENT,
  SchedulerTimezoneNote,
} from 'src/schedules/ScheduleUtils';
import {SCHEDULER_FRAGMENT, SchedulerInfo} from 'src/schedules/SchedulerInfo';
import {SchedulesTable, UnLoadableSchedules} from 'src/schedules/SchedulesRoot';
import {SchedulerRootQuery} from 'src/schedules/types/SchedulerRootQuery';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {Heading, Subheading} from 'src/ui/Text';

export const SchedulerRoot = () => {
  useDocumentTitle('Scheduler');
  const queryResult = useQuery<SchedulerRootQuery>(SCHEDULER_ROOT_QUERY, {
    variables: {},
    fetchPolicy: 'cache-and-network',
  });

  const breadcrumbs: IBreadcrumbProps[] = [{icon: 'time', text: 'Scheduler'}];

  return (
    <ScrollContainer>
      <TopNav breadcrumbs={breadcrumbs} />
      <div style={{padding: '16px'}}>
        <Loading queryResult={queryResult} allowStaleData={true}>
          {(result) => {
            const {scheduler, repositoriesOrError, unLoadableScheduleStates} = result;

            let unLoadableSchedules = null;

            if (repositoriesOrError.__typename === 'PythonError') {
              return <PythonErrorInfo error={repositoriesOrError} />;
            }
            if (unLoadableScheduleStates.__typename === 'PythonError') {
              return <PythonErrorInfo error={unLoadableScheduleStates} />;
            } else if (unLoadableScheduleStates.__typename === 'RepositoryNotFoundError') {
              return (
                <NonIdealState
                  icon={IconNames.ERROR}
                  title="Unexpected RepositoryNotFoundError"
                  description="SchedulerRootQuery unexpectedly returned a RepositoryNotFoundError."
                />
              );
            } else {
              unLoadableSchedules = unLoadableScheduleStates.results;
            }

            const repositoryDefinitionsSection = (
              <Group direction="vertical" spacing={32}>
                <Box
                  flex={{justifyContent: 'space-between', alignItems: 'flex-end'}}
                  padding={{bottom: 12}}
                  border={{side: 'bottom', width: 1, color: Colors.LIGHT_GRAY3}}
                >
                  <Heading>All schedules</Heading>
                  <SchedulerTimezoneNote schedulerOrError={scheduler} />
                </Box>
                {repositoriesOrError.nodes.map((repository) => (
                  <Group direction="vertical" spacing={12} key={repository.name}>
                    <Subheading>{`${repository.name}@${repository.location.name}`}</Subheading>
                    <SchedulesTable repository={repository} />
                  </Group>
                ))}
              </Group>
            );

            return (
              <Group direction="vertical" spacing={32}>
                <SchedulerInfo schedulerOrError={scheduler} />
                {repositoryDefinitionsSection}
                {unLoadableSchedules.length > 0 && (
                  <UnLoadableSchedules unLoadableSchedules={unLoadableSchedules} />
                )}
              </Group>
            );
          }}
        </Loading>
      </div>
    </ScrollContainer>
  );
};

const SCHEDULER_ROOT_QUERY = gql`
  query SchedulerRootQuery {
    repositoriesOrError {
      __typename
      ... on RepositoryConnection {
        nodes {
          id
          ...RepositorySchedulesFragment
        }
      }
      ...PythonErrorFragment
    }
    scheduler {
      ...SchedulerFragment
    }
    unLoadableScheduleStates: scheduleStatesOrError(withNoScheduleDefinition: true) {
      __typename
      ... on ScheduleStates {
        results {
          id
          ...ScheduleStateFragment
        }
      }
      ...PythonErrorFragment
    }
  }

  ${SCHEDULE_DEFINITION_FRAGMENT}
  ${SCHEDULER_FRAGMENT}
  ${PythonErrorInfo.fragments.PythonErrorFragment}
  ${REPOSITORY_SCHEDULES_FRAGMENT}
  ${SCHEDULE_STATE_FRAGMENT}
`;
