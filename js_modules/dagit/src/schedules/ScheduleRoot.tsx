import {Icon} from '@blueprintjs/core';
import gql from 'graphql-tag';
import * as React from 'react';
import {useQuery} from 'react-apollo';
import {RouteComponentProps} from 'react-router';
import {Link} from 'react-router-dom';

import {useScheduleSelector} from 'src/DagsterRepositoryContext';
import {Header, ScrollContainer} from 'src/ListComponents';
import {Loading} from 'src/Loading';
import {ScheduleRow, ScheduleRowHeader} from 'src/schedules/ScheduleRow';
import {SCHEDULE_DEFINITION_FRAGMENT, SchedulerTimezoneNote} from 'src/schedules/ScheduleUtils';
import {ScheduleRootQuery} from 'src/schedules/types/ScheduleRootQuery';

export const ScheduleRoot: React.FunctionComponent<RouteComponentProps<{
  scheduleName: string;
}>> = ({match}) => {
  const {scheduleName} = match.params;
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
          return (
            <ScrollContainer>
              <div style={{display: 'flex'}}>
                <Header>
                  <Link to="/schedules">Schedules</Link>
                  <Icon icon="chevron-right" />
                  {scheduleDefinitionOrError.name}
                </Header>
                <div style={{flex: 1}} />
                <SchedulerTimezoneNote />
              </div>
              <ScheduleRowHeader schedule={scheduleDefinitionOrError} />
              <ScheduleRow schedule={scheduleDefinitionOrError} />
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
