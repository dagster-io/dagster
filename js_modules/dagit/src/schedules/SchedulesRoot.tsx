import * as React from "react";

import {
  Callout,
  Intent,
  Code,
  Card,
  Colors,
  Tooltip,
  PopoverInteractionKind
} from "@blueprintjs/core";
import { Header, Legend, LegendColumn, ScrollContainer } from "../ListComponents";
import { useQuery } from "react-apollo";
import {
  SchedulesRootQuery,
  SchedulesRootQuery_scheduler,
  SchedulesRootQuery_repositoryOrError_Repository,
  SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results,
  SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results
} from "./types/SchedulesRootQuery";
import Loading from "../Loading";
import gql from "graphql-tag";
import PythonErrorInfo from "../PythonErrorInfo";

import { ScheduleRow, ScheduleFragment, ScheduleStateRow } from "./ScheduleRow";

import { useRepositorySelector } from "../DagsterRepositoryContext";
import { ReconcileButton } from "./ReconcileButton";

const getSchedulerSection = (scheduler: SchedulesRootQuery_scheduler) => {
  if (scheduler.__typename === "SchedulerNotDefinedError") {
    return (
      <Callout
        icon="calendar"
        intent={Intent.WARNING}
        title="The current dagster instance does not have a scheduler configured."
        style={{ marginBottom: 40 }}
      >
        <p>
          A scheduler must be configured on the instance to run schedules. Therefore, the schedules
          below are not currently running. You can configure a scheduler on the instance through the{" "}
          <Code>dagster.yaml</Code> file in <Code>$DAGSTER_HOME</Code>
        </p>

        <p>
          See the{" "}
          <a href="https://docs.dagster.io/deploying/instance#instance-configuration-yaml">
            instance configuration documentation
          </a>{" "}
          for more information.
        </p>
      </Callout>
    );
  } else if (scheduler.__typename === "PythonError") {
    return <PythonErrorInfo error={scheduler} />;
  }

  return null;
};

const GetStaleReconcileSection: React.FunctionComponent<{
  scheduleDefinitionsWithoutState: SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results[];
  scheduleStatesWithoutDefinitions: SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results[];
}> = ({ scheduleDefinitionsWithoutState, scheduleStatesWithoutDefinitions }) => {
  if (
    scheduleDefinitionsWithoutState.length === 0 &&
    scheduleStatesWithoutDefinitions.length === 0
  ) {
    return null;
  }

  return (
    <Card style={{ backgroundColor: Colors.LIGHT_GRAY4 }}>
      <Callout intent={Intent.WARNING}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center"
          }}
        >
          <div>
            <p>
              There have been changes to the list of schedule definitions in this repository since
              the last time the scheduler state had been reconciled. For the dagster scheduler to
              run schedules, schedule definitions need to be reconciled with the internal schedule
              storage database.
            </p>
            <p>
              To reconcile schedule state, run <Code>dagster schedule reconcile</Code> or click{" "}
              <ReconcileButton />
            </p>
          </div>
        </div>
      </Callout>
      <ScheduleWithoutStateTable schedules={scheduleDefinitionsWithoutState} />
      <ScheduleStatesWithoutDefinitionsTable scheduleStates={scheduleStatesWithoutDefinitions} />
    </Card>
  );
};

const SchedulesRoot: React.FunctionComponent = () => {
  const repositorySelector = useRepositorySelector();

  const queryResult = useQuery<SchedulesRootQuery>(SCHEDULES_ROOT_QUERY, {
    variables: {
      repositorySelector: repositorySelector
    },
    fetchPolicy: "cache-and-network",
    pollInterval: 50 * 1000,
    partialRefetch: true
  });

  return (
    <Loading queryResult={queryResult} allowStaleData={true}>
      {result => {
        const {
          scheduler,
          repositoryOrError,
          scheduleDefinitionsOrError,
          scheduleStatesOrError: scheduleStatesWithoutDefinitionsOrError
        } = result;
        const schedulerSection = getSchedulerSection(scheduler);
        let staleReconcileSection = null;
        let scheduleDefinitionsSection = null;

        if (scheduleDefinitionsOrError.__typename === "PythonError") {
          scheduleDefinitionsSection = <PythonErrorInfo error={scheduleDefinitionsOrError} />;
        } else if (repositoryOrError.__typename === "PythonError") {
          scheduleDefinitionsSection = <PythonErrorInfo error={repositoryOrError} />;
        } else if (repositoryOrError.__typename === "RepositoryNotFoundError") {
          // Should not be possible, the schedule definitions call will error out
        } else if (scheduleDefinitionsOrError.__typename === "ScheduleDefinitions") {
          const scheduleDefinitions = scheduleDefinitionsOrError.results;
          const scheduleDefinitionsWithState = scheduleDefinitions.filter(s => s.scheduleState);
          const scheduleDefinitionsWithoutState = scheduleDefinitions.filter(s => !s.scheduleState);

          scheduleDefinitionsSection = (
            <ScheduleTable
              schedules={scheduleDefinitionsWithState}
              repository={repositoryOrError}
            />
          );

          if (scheduleStatesWithoutDefinitionsOrError.__typename === "ScheduleStates") {
            const scheduleStatesWithoutDefinitions =
              scheduleStatesWithoutDefinitionsOrError.results;
            staleReconcileSection = (
              <GetStaleReconcileSection
                scheduleDefinitionsWithoutState={scheduleDefinitionsWithoutState}
                scheduleStatesWithoutDefinitions={scheduleStatesWithoutDefinitions}
              />
            );
          }
        }

        return (
          <ScrollContainer>
            {schedulerSection}
            {staleReconcileSection}
            {scheduleDefinitionsSection}
          </ScrollContainer>
        );
      }}
    </Loading>
  );
};

const ScheduleTable: React.FunctionComponent<{
  schedules: SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results[];
  repository: SchedulesRootQuery_repositoryOrError_Repository;
}> = props => {
  if (props.schedules.length === 0) {
    return null;
  }

  return (
    <div style={{ marginTop: 30 }}>
      <Header>{`Schedules`}</Header>
      <div>
        {`${props.schedules.length} loaded from `}
        <Tooltip
          interactionKind={PopoverInteractionKind.HOVER}
          content={
            <pre>
              python: <Code>{props.repository.origin.executablePath}</Code>
              {"\n"}
              code: <Code>{props.repository.origin.codePointerDescription}</Code>
              {"\n"}
              id: <Code>{props.repository.id}</Code>
            </pre>
          }
        >
          <Code>{props.repository.name}</Code>
        </Tooltip>
      </div>

      {props.schedules.length > 0 && (
        <Legend>
          <LegendColumn style={{ maxWidth: 60, paddingRight: 2 }}></LegendColumn>
          <LegendColumn style={{ flex: 1.4 }}>Schedule Name</LegendColumn>
          <LegendColumn>Pipeline</LegendColumn>
          <LegendColumn style={{ maxWidth: 150 }}>Schedule</LegendColumn>
          <LegendColumn style={{ maxWidth: 100 }}>Last Tick</LegendColumn>
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

const ScheduleWithoutStateTable: React.FunctionComponent<{
  schedules: SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results[];
}> = props => {
  if (props.schedules.length === 0) {
    return null;
  }

  return (
    <div style={{ marginTop: 10, marginBottom: 10 }}>
      <h4>New Schedule Definitions</h4>
      <p>
        The following are new schedule definitions for which there are no entries in schedule
        storage yet. After reconciliation, these schedules can be turned on.
      </p>
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

interface ScheduleStateTableProps {
  scheduleStates: SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results[];
}

const ScheduleStatesWithoutDefinitionsTable: React.FunctionComponent<ScheduleStateTableProps> = props => {
  if (props.scheduleStates.length === 0) {
    return null;
  }

  return (
    <div style={{ marginTop: 20, marginBottom: 10 }}>
      <h4>Deleted Schedule Definitions</h4>
      <p>
        The following are entries in schedule storage for which there is no matching schedule
        definition anymore. This means that the schedule definition has been deleted or renamed.
        After reconciliation, these entries will be deleted.
      </p>
      {props.scheduleStates.length > 0 && (
        <Legend>
          <LegendColumn style={{ flex: 1.4 }}>Schedule Name</LegendColumn>
          <LegendColumn style={{ maxWidth: 150 }}>Schedule</LegendColumn>
          <LegendColumn style={{ maxWidth: 100 }}>Last Tick</LegendColumn>
          <LegendColumn style={{ flex: 1 }}>Latest Runs</LegendColumn>
        </Legend>
      )}
      {props.scheduleStates.map(scheduleState => (
        <ScheduleStateRow scheduleState={scheduleState} key={scheduleState.scheduleOriginId} />
      ))}
    </div>
  );
};

export const SCHEDULES_ROOT_QUERY = gql`
  query SchedulesRootQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      __typename
      ... on Repository {
        name
        id
        origin {
          executablePath
          codePointerDescription
        }
      }
      ...PythonErrorFragment
    }
    scheduler {
      __typename
      ... on SchedulerNotDefinedError {
        message
      }
      ...PythonErrorFragment
    }
    scheduleDefinitionsOrError(repositorySelector: $repositorySelector) {
      ... on ScheduleDefinitions {
        results {
          ...ScheduleDefinitionFragment
        }
      }
      ...PythonErrorFragment
    }
    scheduleStatesOrError(repositorySelector: $repositorySelector, withNoScheduleDefinition: true) {
      __typename
      ... on ScheduleStates {
        results {
          ...ScheduleStateFragment
        }
      }
      ...PythonErrorFragment
    }
  }

  ${ScheduleFragment}
  ${PythonErrorInfo.fragments.PythonErrorFragment}
`;

export default SchedulesRoot;
