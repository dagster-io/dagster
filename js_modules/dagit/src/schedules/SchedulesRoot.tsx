import * as React from "react";

import { NonIdealState } from "@blueprintjs/core";
import {
  Header,
  Legend,
  LegendColumn,
  ScrollContainer
} from "../ListComponents";
import { Query, QueryResult } from "react-apollo";
import {
  SchedulesRootQuery,
  SchedulesRootQuery_scheduler_Scheduler_runningSchedules
} from "./types/SchedulesRootQuery";
import Loading from "../Loading";
import gql from "graphql-tag";

import { ScheduleRow, ScheduleRowFragment } from "./ScheduleRow";

const NUM_RUNS_TO_DISPLAY = 10;

export default class SchedulesRoot extends React.Component {
  render() {
    return (
      <Query
        query={SCHEDULES_ROOT_QUERY}
        variables={{
          limit: NUM_RUNS_TO_DISPLAY
        }}
        fetchPolicy="cache-and-network"
        pollInterval={15 * 1000}
        partialRefetch={true}
      >
        {(queryResult: QueryResult<SchedulesRootQuery, any>) => (
          <Loading queryResult={queryResult} allowStaleData={true}>
            {result => {
              const { scheduler } = result;

              if (scheduler.__typename === "SchedulerNotDefinedError") {
                return (
                  <ScrollContainer>
                    <div style={{ marginTop: 100 }}>
                      <NonIdealState
                        icon="calendar"
                        title="Scheduler"
                        description="A scheduler is not defined for this repository."
                      />
                    </div>
                  </ScrollContainer>
                );
              } else if (scheduler.__typename === "PythonError") {
                return (
                  <ScrollContainer>
                    <div style={{ marginTop: 100 }}>
                      <NonIdealState
                        icon="error"
                        title="PythonError"
                        description={scheduler.message}
                      />
                    </div>
                    <pre>{scheduler.stack}</pre>
                  </ScrollContainer>
                );
              } else if (scheduler.runningSchedules.length === 0) {
                return (
                  <ScrollContainer>
                    <div style={{ marginTop: 100 }}>
                      <NonIdealState
                        icon="calendar"
                        title="Scheduler"
                        description="No schedules to display."
                      />
                    </div>
                  </ScrollContainer>
                );
              }

              const sortedRunningSchedules = scheduler.runningSchedules.sort(
                (a, b) =>
                  a.scheduleDefinition.name.localeCompare(
                    b.scheduleDefinition.name
                  )
              );

              return (
                <>
                  <ScrollContainer>
                    <ScheduleTable schedules={sortedRunningSchedules} />
                  </ScrollContainer>
                </>
              );
            }}
          </Loading>
        )}
      </Query>
    );
  }
}

interface ScheduleTableProps {
  schedules: SchedulesRootQuery_scheduler_Scheduler_runningSchedules[];
}

const ScheduleTable: React.FunctionComponent<ScheduleTableProps> = props => {
  return (
    <div>
      <Header>{`Schedule (${props.schedules.length})`}</Header>
      {props.schedules.length > 0 && (
        <Legend>
          <LegendColumn
            style={{ maxWidth: 60, paddingRight: 2 }}
          ></LegendColumn>
          <LegendColumn style={{ flex: 1.4 }}>Schedule Name</LegendColumn>
          <LegendColumn>Pipeline</LegendColumn>
          <LegendColumn style={{ maxWidth: 150 }}>Schedule</LegendColumn>
          <LegendColumn style={{ flex: 1 }}>Recent Attempts</LegendColumn>
          <LegendColumn style={{ flex: 1 }}>Last Attempt</LegendColumn>
          <LegendColumn style={{ flex: 1 }}>Execution Params</LegendColumn>
        </Legend>
      )}
      {props.schedules.map(schedule => (
        <ScheduleRow schedule={schedule} key={schedule.id} />
      ))}
    </div>
  );
};

export const SCHEDULES_ROOT_QUERY = gql`
  query SchedulesRootQuery($limit: Int!) {
    scheduler {
      __typename
      ... on SchedulerNotDefinedError {
        message
      }
      ... on Scheduler {
        runningSchedules {
          ...ScheduleFragment
        }
      }
      ... on SchedulerNotDefinedError {
        message
      }
      ... on PythonError {
        message
        stack
      }
    }
  }

  ${ScheduleRowFragment}
`;
