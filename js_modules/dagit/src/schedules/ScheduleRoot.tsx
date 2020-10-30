import {gql, useQuery} from '@apollo/client';
import {IBreadcrumbProps} from '@blueprintjs/core';
import * as React from 'react';

import {ScrollContainer} from 'src/ListComponents';
import {Loading} from 'src/Loading';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {TopNav} from 'src/nav/TopNav';
import {ScheduleRow, ScheduleRowHeader} from 'src/schedules/ScheduleRow';
import {SCHEDULE_DEFINITION_FRAGMENT, SchedulerTimezoneNote} from 'src/schedules/ScheduleUtils';
import {ScheduleRootQuery} from 'src/schedules/types/ScheduleRootQuery';
import {Page} from 'src/ui/Page';
import {Table} from 'src/ui/Table';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

interface Props {
  scheduleName: string;
  repoAddress: RepoAddress;
}

export const ScheduleRoot: React.FC<Props> = (props) => {
  const {scheduleName, repoAddress} = props;
  useDocumentTitle(`Schedule: ${scheduleName}`);

  const scheduleSelector = {
    ...repoAddressToSelector(repoAddress),
    scheduleName,
  };

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
            {
              icon: 'time',
              text: 'Schedules',
              href: workspacePathFromAddress(repoAddress, '/schedules'),
            },
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
                    <ScheduleRow repoAddress={repoAddress} schedule={scheduleDefinitionOrError} />
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
