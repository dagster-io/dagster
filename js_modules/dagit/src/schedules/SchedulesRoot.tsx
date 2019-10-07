import * as React from "react";
import * as qs from "query-string";
import { useMutation } from "@apollo/react-hooks";

import {
  Button,
  Classes,
  Switch,
  Icon,
  Menu,
  MenuItem,
  MenuDivider,
  Popover,
  NonIdealState,
  Tooltip
} from "@blueprintjs/core";
import { HighlightedCodeBlock } from "../HighlightedCodeBlock";
import {
  Header,
  Legend,
  LegendColumn,
  RowColumn,
  RowContainer,
  ScrollContainer
} from "../ListComponents";
import {
  RunStatus,
  titleForRun,
  unixTimestampToString
} from "../runs/RunUtils";
import { Query, QueryResult } from "react-apollo";
import {
  SchedulesRootQuery,
  SchedulesRootQuery_scheduler_Scheduler_runningSchedules,
  SchedulesRootQuery_scheduler_Scheduler_runningSchedules_runs
} from "./types/SchedulesRootQuery";
import { ScheduleStatus } from "../types/globalTypes";
import { Link } from "react-router-dom";
import Loading from "../Loading";
import cronstrue from "cronstrue";
import gql from "graphql-tag";
import { showCustomAlert } from "../CustomAlertProvider";
import styled from "styled-components";
import { DataProxy } from "apollo-cache";
import { copyValue } from "../Util";

export default class SchedulesRoot extends React.Component {
  render() {
    return (
      <Query
        query={SCHEDULES_ROOT_QUERY}
        fetchPolicy="cache-and-network"
        pollInterval={15 * 1000}
        partialRefetch={true}
      >
        {(queryResult: QueryResult<SchedulesRootQuery, any>) => (
          <Loading queryResult={queryResult}>
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
                  );
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
          <LegendColumn style={{ flex: 1 }}>Recent Runs</LegendColumn>
          <LegendColumn style={{ flex: 1 }}>Last Run</LegendColumn>
          <LegendColumn style={{ flex: 1 }}>Execution Params</LegendColumn>
        </Legend>
      )}
      {props.schedules.map(schedule => (
        <ScheduleRow schedule={schedule} key={schedule.scheduleId} />
      ))}
    </div>
  );
};

const ScheduleRow: React.FunctionComponent<{
  schedule: SchedulesRootQuery_scheduler_Scheduler_runningSchedules;
}> = ({ schedule }) => {
  const { scheduleId, status, scheduleDefinition, runs, logsPath } = schedule;
  const {
    name,
    cronSchedule,
    executionParamsString,
    environmentConfigYaml
  } = scheduleDefinition;
  const executionParams = JSON.parse(executionParamsString);
  const pipelineName = executionParams.selector.name;
  const mode = executionParams.mode;

  const [startSchedule] = useMutation(START_SCHEDULE_MUTATION);
  const [stopSchedule] = useMutation(STOP_SCHEDULE_MUTATION);

  const getNaturalLanguageCronString = (cronSchedule: string) => {
    try {
      return cronstrue.toString(cronSchedule);
    } catch {
      return "Invalid cron string";
    }
  };
  const NUM_RUNS_TO_DISPLAY = 10;

  const sortRuns = (
    runs: SchedulesRootQuery_scheduler_Scheduler_runningSchedules_runs[]
  ) => {
    if (!runs) return [];

    return runs.sort((a, b) => {
      const aStart = a.stats.startTime || Number.MAX_SAFE_INTEGER;
      const bStart = b.stats.startTime || Number.MAX_SAFE_INTEGER;
      return bStart - aStart;
    });
  };

  const sortedRuns = sortRuns(runs);
  const mostRecentRun = sortedRuns[0];

  const optimisticUpdateStore = (
    store: DataProxy,
    name: string,
    status: ScheduleStatus
  ) => {
    const data: SchedulesRootQuery | null = store.readQuery({
      query: SCHEDULES_ROOT_QUERY
    });
    if (data && data.scheduler.__typename === "Scheduler") {
      data.scheduler.runningSchedules = data.scheduler.runningSchedules.map(
        schedule => {
          if (schedule.scheduleDefinition.name === name) {
            schedule.status = status;
          }
          return schedule;
        }
      );
      store.writeQuery({
        query: SCHEDULES_ROOT_QUERY,
        data: data
      });
    }
  };

  return (
    <RowContainer key={name}>
      <RowColumn style={{ maxWidth: 60, paddingLeft: 0, textAlign: "center" }}>
        <Switch
          checked={status === ScheduleStatus.RUNNING}
          large={true}
          innerLabelChecked="on"
          innerLabel="off"
          onChange={() => {
            if (status === ScheduleStatus.RUNNING) {
              stopSchedule({
                variables: { scheduleName: name },
                update: store =>
                  optimisticUpdateStore(store, name, ScheduleStatus.STOPPED)
              });
            } else {
              startSchedule({
                variables: { scheduleName: name },
                update: store =>
                  optimisticUpdateStore(store, name, ScheduleStatus.RUNNING)
              });
            }
          }}
        />
      </RowColumn>
      <RowColumn style={{ flex: 1.4 }}>
        <ScheduleName>{name}</ScheduleName>
      </RowColumn>
      <RowColumn>
        <Link style={{ display: "block" }} to={`/p/${pipelineName}/explore/`}>
          <Icon icon="diagram-tree" /> {pipelineName}
        </Link>
      </RowColumn>
      <RowColumn
        style={{
          maxWidth: 150
        }}
      >
        <Tooltip
          className={Classes.TOOLTIP_INDICATOR}
          position={"top"}
          content={cronSchedule}
        >
          {getNaturalLanguageCronString(cronSchedule)}
        </Tooltip>
      </RowColumn>
      <RowColumn style={{ flex: 1 }}>
        {runs && runs.length > 0
          ? runs.slice(0, NUM_RUNS_TO_DISPLAY).map(run => (
              <div
                style={{ display: "inline", cursor: "pointer", marginRight: 5 }}
                key={run.runId}
              >
                <Link to={`/p/${run.pipeline.name}/runs/${run.runId}`}>
                  <Tooltip position={"top"} content={titleForRun(run)}>
                    <RunStatus status={run.status} />
                  </Tooltip>
                </Link>
              </div>
            ))
          : "-"}
        {runs && runs.length > NUM_RUNS_TO_DISPLAY && (
          <Link
            to={`/runs?q=tag:${encodeURIComponent(
              "dagster/schedule_id"
            )}=${scheduleId}`}
          >
            {" "}
            +{runs.length - NUM_RUNS_TO_DISPLAY} more
          </Link>
        )}
      </RowColumn>
      <RowColumn style={{ flex: 1 }}>
        {mostRecentRun
          ? unixTimestampToString(mostRecentRun.stats.startTime)
          : "No previous runs"}
      </RowColumn>
      <RowColumn
        style={{
          display: "flex",
          alignItems: "flex-start",
          flex: 1
        }}
      >
        <div style={{ flex: 1 }}>
          <div>{`Mode: ${mode}`}</div>
        </div>
        <Popover
          content={
            <Menu>
              <MenuItem
                text="View Execution Params..."
                icon="share"
                onClick={() =>
                  showCustomAlert({
                    title: "Execution Params",
                    body: (
                      <HighlightedCodeBlock
                        value={JSON.stringify(executionParams, null, 2)}
                        languages={["json"]}
                      />
                    )
                  })
                }
              />
              <MenuItem
                text="Copy Path to Debug Logs"
                icon="clipboard"
                onClick={(e: React.MouseEvent<any>) => copyValue(e, logsPath)}
              />
              <MenuDivider />
              <MenuItem
                text="Open in Execute Tab..."
                icon="edit"
                target="_blank"
                href={`/p/${
                  executionParams.selector.name
                }/execute/setup?${qs.stringify({
                  mode: executionParams.mode,
                  config: environmentConfigYaml,
                  solidSubset: executionParams.selector.solidSubset
                })}`}
              />
            </Menu>
          }
          position={"bottom"}
        >
          <Button minimal={true} icon="chevron-down" />
        </Popover>
      </RowColumn>
    </RowContainer>
  );
};

const ScheduleName = styled.pre`
  margin: 0;
`;

const START_SCHEDULE_MUTATION = gql`
  mutation StartSchedule($scheduleName: String!) {
    startSchedule(scheduleName: $scheduleName) {
      schedule {
        status
      }
    }
  }
`;

const STOP_SCHEDULE_MUTATION = gql`
  mutation StopSchedule($scheduleName: String!) {
    stopRunningSchedule(scheduleName: $scheduleName) {
      schedule {
        scheduleId
        status
      }
    }
  }
`;
export const SCHEDULES_ROOT_QUERY = gql`
  query SchedulesRootQuery {
    scheduler {
      __typename
      ... on SchedulerNotDefinedError {
        message
      }
      ... on Scheduler {
        runningSchedules {
          scheduleId
          scheduleDefinition {
            name
            executionParamsString
            environmentConfigYaml
            cronSchedule
          }
          logsPath
          runs {
            runId
            pipeline {
              name
            }
            status
            stats {
              startTime
            }
          }
          status
        }
      }
      ... on SchedulerNotDefinedError {
        message
      }
    }
  }
`;
