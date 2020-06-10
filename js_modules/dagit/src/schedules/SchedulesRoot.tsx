import * as React from "react";

import { NonIdealState, Callout, Intent, Code } from "@blueprintjs/core";
import {
  Header,
  Legend,
  LegendColumn,
  ScrollContainer
} from "../ListComponents";
import { Query, QueryResult } from "react-apollo";
import {
  SchedulesRootQuery,
  SchedulesRootQuery_scheduler,
  SchedulesRootQuery_schedules
} from "./types/SchedulesRootQuery";
import Loading from "../Loading";
import gql from "graphql-tag";

import { ScheduleRow, ScheduleRowFragment } from "./ScheduleRow";

const NUM_RUNS_TO_DISPLAY = 10;

const getSchedulerError = (scheduler: SchedulesRootQuery_scheduler) => {
  if (scheduler.__typename === "SchedulerNotDefinedError") {
    return (
      <Callout
        icon="calendar"
        intent={Intent.WARNING}
        title="The current dagster instance does not have a scheduler configured."
        style={{ marginBottom: 40 }}
      >
        <p>
          A scheduler must be configured on the instance to run schedules.
          Therefore, the schedules below are not currently running. You can
          configure a scheduler on the instance through the{" "}
          <Code>dagster.yaml</Code> file in <Code>$DAGSTER_HOME</Code>
        </p>

        <p>
          See the{" "}
          <a href="https://docs.dagster.io/docs/deploying/instance#instance-configuration-yaml">
            instance configuration documentation
          </a>{" "}
          for more information.
        </p>
      </Callout>
    );
  } else if (scheduler.__typename === "PythonError") {
    return (
      <>
        <div>
          <NonIdealState
            icon="error"
            title="PythonError"
            description={scheduler.message}
          />
        </div>
        <pre>{scheduler.stack}</pre>
      </>
    );
  }

  return null;
};

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
              const { scheduler, schedules } = result;

              const schedulerError = getSchedulerError(scheduler);

              if (schedules.length === 0) {
                return (
                  <ScrollContainer>
                    <div style={{ marginTop: 100 }}>
                      {schedulerError}
                      <NonIdealState
                        icon="calendar"
                        title="Scheduler"
                        description="No schedules to display."
                      />
                    </div>
                  </ScrollContainer>
                );
              }

              const sortedRunningSchedules = schedules.sort((a, b) =>
                a.scheduleDefinition.name.localeCompare(
                  b.scheduleDefinition.name
                )
              );

              return (
                <>
                  <ScrollContainer>
                    {schedulerError}
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
  schedules: SchedulesRootQuery_schedules[];
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
          <LegendColumn style={{ flex: 1 }}>Schedule Tick Stats</LegendColumn>
          <LegendColumn style={{ flex: 1 }}>Latest Runs</LegendColumn>
          <LegendColumn style={{ flex: 1 }}>Execution Params</LegendColumn>
        </Legend>
      )}
      {props.schedules.map(schedule => (
        <ScheduleRow
          schedule={schedule}
          key={schedule.scheduleDefinition.name}
        />
      ))}
    </div>
  );
};

export const SCHEDULES_ROOT_QUERY = gql`
  query SchedulesRootQuery($limit: Int!) {
    schedules {
      ...ScheduleFragment
    }
    scheduler {
      __typename
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
