import {IBreadcrumbProps} from '@blueprintjs/core';
import gql from 'graphql-tag';
import * as React from 'react';
import {useQuery} from 'react-apollo';
import {RouteComponentProps} from 'react-router';

import {useScheduleSelector} from 'src/DagsterRepositoryContext';
import {ScrollContainer} from 'src/ListComponents';
import {Loading} from 'src/Loading';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {TopNav} from 'src/nav/TopNav';
import {ScheduleRow, ScheduleRowHeader} from 'src/schedules/ScheduleRow';
import {SCHEDULE_DEFINITION_FRAGMENT, SchedulerTimezoneNote} from 'src/schedules/ScheduleUtils';
import {ScheduleRootQuery} from 'src/schedules/types/ScheduleRootQuery';
import {Page} from 'src/ui/Page';
import {Table} from 'src/ui/Table';

export const ScheduleRoot: React.FunctionComponent<RouteComponentProps<{
  scheduleName: string;
}>> = ({match}) => {
  const {scheduleName} = match.params;
  useDocumentTitle(`Schedule: ${scheduleName}`);
  const scheduleSelector = useScheduleSelector(scheduleName);
  const queryResult = useQuery<ScheduleRootQuery>(SCHEDULE_ROOT_QUERY, {
    variables: {
      scheduleSelector,
    },
    fetchPolicy: 'cache-and-network',
    pollInterval: 15 * 1000,
    partialRefetch: true,
  });

  return (
    <Loading queryResult={queryResult} allowStaleData={true}>
      {({scheduleDefinitionOrError}) => {
        if (scheduleDefinitionOrError.__typename === 'ScheduleDefinition') {
          const breadcrumbs: IBreadcrumbProps[] = [
            {icon: 'time', text: 'Schedules', href: '/schedules'},
            {text: scheduleDefinitionOrError.name},
          ];

          return (
            <ScrollContainer>
              <TopNav breadcrumbs={breadcrumbs} />
              <Page>
                <SchedulerTimezoneNote />
                <Table striped style={{width: '100%'}}>
                  <thead>
                    <ScheduleRowHeader schedule={scheduleDefinitionOrError} />
                  </thead>
                  <tbody>
                    <ScheduleRow schedule={scheduleDefinitionOrError} />
                  </tbody>
                </Table>
              </Page>
            </ScrollContainer>
          );
        } else {
          return null;
        }
      }}
    </Loading>
  );
};

export const SCHEDULE_ROOT_QUERY = gql`
  query ScheduleRootQuery($scheduleSelector: ScheduleSelector!) {
    scheduleDefinitionOrError(scheduleSelector: $scheduleSelector) {
      ... on ScheduleDefinition {
        ...ScheduleDefinitionFragment
      }
      ... on ScheduleDefinitionNotFoundError {
        message
      }
      ... on PythonError {
        message
        stack
      }
    }
  }

  ${SCHEDULE_DEFINITION_FRAGMENT}
`;
