import * as React from "react";

import { Header, ScrollContainer } from "../ListComponents";
import { useQuery } from "react-apollo";
import Loading from "../Loading";
import gql from "graphql-tag";
import { RouteComponentProps } from "react-router";
import { Link } from "react-router-dom";
import { ScheduleRootQuery } from "./types/ScheduleRootQuery";
import { Icon } from "@blueprintjs/core";
import { ScheduleRow, ScheduleRowHeader } from "./ScheduleRow";

import { __RouterContext as RouterContext } from "react-router";
import * as querystring from "query-string";
import { PartitionView } from "../partitions/PartitionView";
import { useScheduleSelector } from "../DagsterRepositoryContext";
import { SCHEDULE_DEFINITION_FRAGMENT, SchedulerTimezoneNote } from "./ScheduleUtils";

export const ScheduleRoot: React.FunctionComponent<RouteComponentProps<{
  scheduleName: string;
}>> = ({ match, location }) => {
  const { scheduleName } = match.params;
  const scheduleSelector = useScheduleSelector(scheduleName);
  const { history } = React.useContext(RouterContext);
  const qs = querystring.parse(location.search);
  const cursor = (qs.cursor as string) || undefined;
  const setCursor = (cursor: string | undefined) => {
    history.push({ search: `?${querystring.stringify({ ...qs, cursor })}` });
  };
  const queryResult = useQuery<ScheduleRootQuery>(SCHEDULE_ROOT_QUERY, {
    variables: {
      scheduleSelector
    },
    fetchPolicy: "cache-and-network",
    pollInterval: 15 * 1000,
    partialRefetch: true
  });

  return (
    <Loading queryResult={queryResult} allowStaleData={true}>
      {result => {
        const { scheduleDefinitionOrError } = result;

        if (scheduleDefinitionOrError.__typename === "ScheduleDefinition") {
          const partitionSetName = scheduleDefinitionOrError.partitionSet?.name;
          return (
            <ScrollContainer>
              <div style={{ display: "flex" }}>
                <Header>
                  <Link to="/schedules">Schedules</Link>
                  <Icon icon="chevron-right" />
                  {scheduleDefinitionOrError.name}
                </Header>
                <div style={{ flex: 1 }} />
                <SchedulerTimezoneNote />
              </div>
              <ScheduleRowHeader schedule={scheduleDefinitionOrError} />
              <ScheduleRow schedule={scheduleDefinitionOrError} />
              {partitionSetName ? (
                <PartitionView
                  pipelineName={scheduleDefinitionOrError.pipelineName}
                  partitionSetName={partitionSetName}
                  cursor={cursor}
                  setCursor={setCursor}
                />
              ) : null}
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
