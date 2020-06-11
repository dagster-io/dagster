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
  SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results
} from "./types/SchedulesRootQuery";
import Loading from "../Loading";
import gql from "graphql-tag";

import { ScheduleRow, ScheduleFragment } from "./ScheduleRow";

import { useRepositorySelector } from "../DagsterRepositoryContext";

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

const SchedulesRoot: React.FunctionComponent = () => {
  const repositorySelector = useRepositorySelector();

  return (
    <Query
      query={SCHEDULES_ROOT_QUERY}
      variables={{
        repositorySelector: repositorySelector,
        limit: NUM_RUNS_TO_DISPLAY
      }}
      fetchPolicy="cache-and-network"
      pollInterval={15 * 1000}
      partialRefetch={true}
    >
      {(queryResult: QueryResult<SchedulesRootQuery, any>) => (
        <Loading queryResult={queryResult} allowStaleData={true}>
          {result => {
            const { scheduler, scheduleDefinitionsOrError } = result;

            const schedulerError = getSchedulerError(scheduler);

            if (
              scheduleDefinitionsOrError.__typename === "ScheduleDefinitions"
            ) {
              const schedules = scheduleDefinitionsOrError.results;
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

              const sortedScheduleDefinitions = schedules.sort((a, b) =>
                a.name.localeCompare(b.name)
              );

              return (
                <>
                  <ScrollContainer>
                    {schedulerError}
                    <ScheduleWithoutStateTable
                      schedules={sortedScheduleDefinitions.filter(
                        s => !s.scheduleState
                      )}
                    />
                    <ScheduleTable
                      schedules={sortedScheduleDefinitions.filter(
                        s => s.scheduleState
                      )}
                    />
                  </ScrollContainer>
                </>
              );
            }

            return null;
          }}
        </Loading>
      )}
    </Query>
  );
};

interface ScheduleTableProps {
  schedules: SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results[];
}

const ScheduleTable: React.FunctionComponent<ScheduleTableProps> = props => {
  return (
    <div style={{ marginTop: 30 }}>
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
        <ScheduleRow schedule={schedule} key={schedule.name} />
      ))}
    </div>
  );
};

const ScheduleWithoutStateTable: React.FunctionComponent<ScheduleTableProps> = props => {
  if (props.schedules.length == 0) {
    return null;
  }

  return (
    <div style={{ marginTop: 10, marginBottom: 10 }}>
      <Callout intent={Intent.WARNING}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center"
          }}
        >
          <div>
            The following schedules are not reconciled. Run{" "}
            <Code>dagster schedule up</Code> to reconcile.{" "}
          </div>
        </div>
      </Callout>
      {props.schedules.length > 0 && (
        <Legend>
          <LegendColumn style={{ flex: 1.4 }}>Schedule Name</LegendColumn>
          <LegendColumn>Pipeline</LegendColumn>
          <LegendColumn style={{ maxWidth: 150 }}>Schedule</LegendColumn>
          <LegendColumn style={{ flex: 1 }}>Execution Params</LegendColumn>
        </Legend>
      )}
      {props.schedules.map(schedule => (
        <ScheduleRow schedule={schedule} key={schedule.name} />
      ))}
    </div>
  );
};

export const SCHEDULES_ROOT_QUERY = gql`
  query SchedulesRootQuery(
    $repositorySelector: RepositorySelector!
    $limit: Int!
  ) {
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
    scheduleDefinitionsOrError(repositorySelector: $repositorySelector) {
      ... on ScheduleDefinitions {
        results {
          ...ScheduleDefinitionFragment
        }
      }
    }
  }

  ${ScheduleFragment}
`;

export default SchedulesRoot;
