import * as React from "react";

import {
  Button,
  Classes,
  Colors,
  Icon,
  Menu,
  MenuItem,
  Popover,
  Tooltip
} from "@blueprintjs/core";
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
  SchedulesRootQuery_scheduler_Scheduler_runningSchedules_runs,
  SchedulesRootQuery_schedules
} from "./types/SchedulesRootQuery";

import { Link } from "react-router-dom";
import Loading from "../Loading";
import cronstrue from "cronstrue";
import gql from "graphql-tag";
import { showCustomAlert } from "../CustomAlertProvider";
import styled from "styled-components";

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
              let runningSchedules: SchedulesRootQuery_scheduler_Scheduler_runningSchedules[] = [];
              if (result.scheduler.__typename === "Scheduler") {
                runningSchedules = result.scheduler.runningSchedules;
              }

              return (
                <>
                  <ScrollContainer>
                    <ScheduleTable
                      schedules={result.schedules}
                      runningSchedules={runningSchedules}
                    />
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
  schedules: SchedulesRootQuery_schedules[];
  runningSchedules: SchedulesRootQuery_scheduler_Scheduler_runningSchedules[];
}

const ScheduleTable: React.FunctionComponent<ScheduleTableProps> = props => {
  const runningScheduleMap = {};
  props.runningSchedules.forEach(runningSchedule => {
    runningScheduleMap[
      runningSchedule.scheduleDefinition.name
    ] = runningSchedule;
  });

  return (
    <div>
      <Header>{`Schedule Definitions (${props.schedules.length})`}</Header>
      {props.schedules.length > 0 && (
        <Legend>
          <LegendColumn style={{ maxWidth: 40 }}></LegendColumn>
          <LegendColumn style={{ flex: 1.4 }}>Schedule Name</LegendColumn>
          <LegendColumn>Pipeline</LegendColumn>
          <LegendColumn style={{ maxWidth: 150 }}>Schedule</LegendColumn>
          <LegendColumn style={{ flex: 1 }}>Recent Runs</LegendColumn>
          <LegendColumn style={{ flex: 1 }}>Last Run</LegendColumn>
          <LegendColumn style={{ flex: 1 }}>Execution Params</LegendColumn>
        </Legend>
      )}
      {props.schedules.map(schedule => (
        <ScheduleRow
          schedule={schedule}
          running={runningScheduleMap[schedule.name]}
          runs={
            runningScheduleMap[schedule.name] &&
            runningScheduleMap[schedule.name].runs
          }
          key={schedule.name}
        />
      ))}
    </div>
  );
};

const PipelineRunningDot = styled.div`
  display: inline-block;
  width: 11px;
  height: 11px;
  border-radius: 5.5px;
  align-self: center;
  transition: background 200ms linear;
  background: ${Colors.GREEN1};
`;

const ScheduleRow: React.FunctionComponent<{
  schedule: SchedulesRootQuery_schedules;
  running: boolean;
  runs: SchedulesRootQuery_scheduler_Scheduler_runningSchedules_runs[];
}> = ({ schedule, running, runs }) => {
  const { name, cronSchedule, executionParamsString } = schedule;
  const executionParams = JSON.parse(executionParamsString);
  const pipelineName = executionParams.selector.name;
  const mode = executionParams.mode;

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

  return (
    <RowContainer key={name}>
      <RowColumn style={{ maxWidth: 30, paddingLeft: 0, textAlign: "center" }}>
        {running && <PipelineRunningDot />}
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
          ? runs.slice(1, NUM_RUNS_TO_DISPLAY).map(run => (
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
          <Link to={""}> +{runs.length - NUM_RUNS_TO_DISPLAY} more</Link>
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
                    title: "Config",
                    body: JSON.stringify(executionParams, null, 2)
                  })
                }
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
export const SCHEDULES_ROOT_QUERY = gql`
  query SchedulesRootQuery {
    schedules {
      name
      executionParamsString
      cronSchedule
    }
    scheduler {
      ... on Scheduler {
        runningSchedules {
          scheduleDefinition {
            name
          }
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
        }
      }
      ... on SchedulerNotDefinedError {
        message
      }
    }
  }
`;
