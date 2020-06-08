import * as React from "react";
import * as qs from "query-string";
import { useMutation } from "@apollo/react-hooks";

import {
  Button,
  Switch,
  Icon,
  Menu,
  MenuItem,
  MenuDivider,
  Popover,
  Tooltip,
  Tag,
  Intent,
  PopoverInteractionKind,
  Position
} from "@blueprintjs/core";
import { HighlightedCodeBlock } from "../HighlightedCodeBlock";
import { RowColumn, RowContainer } from "../ListComponents";
import { ScheduleFragment } from "./types/ScheduleFragment";
import {
  StartSchedule,
  StartSchedule_startSchedule_PythonError
} from "./types/StartSchedule";
import {
  StopSchedule,
  StopSchedule_stopRunningSchedule_PythonError
} from "./types/StopSchedule";
import { ScheduleStatus, ScheduleTickStatus } from "../types/globalTypes";

import { Link, useRouteMatch } from "react-router-dom";
import cronstrue from "cronstrue";
import gql from "graphql-tag";
import { showCustomAlert } from "../CustomAlertProvider";
import styled from "styled-components/macro";
import { titleForRun, RunStatus } from "../runs/RunUtils";
import PythonErrorInfo from "../PythonErrorInfo";

const NUM_RUNS_TO_DISPLAY = 10;

const getNaturalLanguageCronString = (cronSchedule: string) => {
  try {
    return cronstrue.toString(cronSchedule);
  } catch {
    return "Invalid cron string";
  }
};

const errorDisplay = (status: ScheduleStatus, runningScheduleCount: number) => {
  if (status === ScheduleStatus.STOPPED && runningScheduleCount === 0) {
    return null;
  } else if (status === ScheduleStatus.RUNNING && runningScheduleCount === 1) {
    return null;
  }

  const errors = [];
  if (status === ScheduleStatus.RUNNING && runningScheduleCount === 0) {
    errors.push(
      "Schedule is set to be running, but the scheduler is not running the schedule"
    );
  } else if (status === ScheduleStatus.STOPPED && runningScheduleCount > 0) {
    errors.push(
      "Schedule is set to be stopped, but the scheduler is still running the schedule"
    );
  }

  if (runningScheduleCount > 0) {
    errors.push("Duplicate cron job for schedule found.");
  }

  return (
    <Popover
      interactionKind={PopoverInteractionKind.CLICK}
      popoverClassName="bp3-popover-content-sizing"
      position={Position.RIGHT}
      fill={true}
    >
      <Tag fill={true} interactive={true} intent={Intent.DANGER}>
        Error
      </Tag>
      <div>
        <h3>There are errors with this schedule.</h3>

        <p>To resolve, run `dagster schedule up`.</p>
        <p>Errors:</p>
        <ul>
          {errors.map((error, index) => (
            <li key={index}>{error}</li>
          ))}
        </ul>
      </div>
    </Popover>
  );
};

export const ScheduleRow: React.FunctionComponent<{
  schedule: ScheduleFragment;
}> = ({ schedule }) => {
  const {
    status,
    scheduleDefinition,
    runningScheduleCount,
    stats,
    ticks,
    runs,
    runsCount
  } = schedule;
  const {
    name,
    cronSchedule,
    pipelineName,
    solidSelection,
    mode,
    runConfigYaml
  } = scheduleDefinition;

  const displayScheduleMutationErrors = (
    data: StartSchedule | StopSchedule
  ) => {
    let error:
      | StartSchedule_startSchedule_PythonError
      | StopSchedule_stopRunningSchedule_PythonError
      | null = null;

    if (
      "startSchedule" in data &&
      data.startSchedule.__typename === "PythonError"
    ) {
      error = data.startSchedule;
    } else if (
      "stopRunningSchedule" in data &&
      data.stopRunningSchedule.__typename === "PythonError"
    ) {
      error = data.stopRunningSchedule;
    }

    if (error) {
      showCustomAlert({
        title: "Schedule Response",
        body: (
          <>
            <PythonErrorInfo error={error} />
          </>
        )
      });
    }
  };

  const [startSchedule] = useMutation(START_SCHEDULE_MUTATION, {
    onCompleted: displayScheduleMutationErrors
  });
  const [stopSchedule] = useMutation(STOP_SCHEDULE_MUTATION, {
    onCompleted: displayScheduleMutationErrors
  });

  const match = useRouteMatch("/schedules/:scheduleName");

  const latestTick = ticks.length > 0 ? ticks[0] : null;

  const displayName = match ? (
    <ScheduleName>{name}</ScheduleName>
  ) : (
    <Link to={`/schedules/${name}`}>
      <ScheduleName>{name}</ScheduleName>
    </Link>
  );

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
                variables: { scheduleName: name }
              });
            } else {
              startSchedule({
                variables: { scheduleName: name }
              });
            }
          }}
        />

        {errorDisplay(status, runningScheduleCount)}
      </RowColumn>
      <RowColumn style={{ flex: 1.4 }}>{displayName}</RowColumn>
      <RowColumn>
        <Link to={`/pipeline/${pipelineName}/`}>
          <Icon icon="diagram-tree" /> {pipelineName}
        </Link>
      </RowColumn>
      <RowColumn
        style={{
          maxWidth: 150
        }}
      >
        <div
          style={{
            position: "relative",
            width: "100%",
            whiteSpace: "pre-wrap",
            display: "block"
          }}
        >
          {cronSchedule ? (
            <Tooltip position={"bottom"} content={cronSchedule}>
              {getNaturalLanguageCronString(cronSchedule)}
            </Tooltip>
          ) : (
            <div>-</div>
          )}
        </div>
      </RowColumn>
      <RowColumn style={{ flex: 1, textAlign: "center" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-around"
          }}
        >
          <Stat>
            <StatNumber>{stats.ticksStarted}</StatNumber> Running
          </Stat>
          <Stat>
            <StatNumber>{stats.ticksSkipped}</StatNumber> Skipped
          </Stat>
          <Stat>
            <StatNumber>{stats.ticksSucceeded}</StatNumber> Succeeded
          </Stat>
          <Stat>
            <StatNumber>{stats.ticksFailed}</StatNumber> Failed
          </Stat>
        </div>
        <div>
          {latestTick && latestTick.status === ScheduleTickStatus.FAILURE && (
            <ErrorTag>
              <Tag fill={true} minimal={true} intent={Intent.WARNING}>
                Latest Attempt failed
              </Tag>
            </ErrorTag>
          )}
        </div>
      </RowColumn>
      <RowColumn
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between"
        }}
      >
        <div>
          {runs.map(run => {
            return (
              <div
                style={{
                  display: "inline-block",
                  cursor: "pointer",
                  marginRight: 5
                }}
                key={run.runId}
              >
                <Link to={`/runs/${run.pipeline.name}/${run.runId}`}>
                  <Tooltip
                    position={"top"}
                    content={titleForRun(run)}
                    wrapperTagName="div"
                    targetTagName="div"
                  >
                    <RunStatus status={run.status} />
                  </Tooltip>
                </Link>
              </div>
            );
          })}

          {runsCount > NUM_RUNS_TO_DISPLAY && (
            <Link
              to={`/runs/?q=${encodeURIComponent(
                `tag:dagster/schedule_name=${name}`
              )}`}
              style={{ verticalAlign: "top" }}
            >
              {" "}
              +{runsCount - NUM_RUNS_TO_DISPLAY} more
            </Link>
          )}
        </div>
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
                text="View Configuration..."
                icon="share"
                onClick={() =>
                  showCustomAlert({
                    title: "Config",
                    body: (
                      <HighlightedCodeBlock
                        value={runConfigYaml || "Unable to resolve config"}
                        languages={["yaml"]}
                      />
                    )
                  })
                }
              />
              {runConfigYaml !== null ? (
                <MenuItem
                  text="Open in Playground..."
                  icon="edit"
                  target="_blank"
                  href={`/pipeline/${pipelineName}/playground/setup?${qs.stringify(
                    {
                      mode,
                      solidSelection,
                      config: runConfigYaml
                    }
                  )}`}
                />
              ) : (
                <MenuItem
                  text="Open in Playground..."
                  icon="edit"
                  disabled={true}
                />
              )}
              <MenuDivider />
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

export const ScheduleRowFragment = gql`
  fragment ScheduleFragment on RunningSchedule {
    __typename
    runningScheduleCount
    scheduleDefinition {
      name
      cronSchedule
      pipelineName
      solidSelection
      mode
      runConfigYaml
    }
    ticks(limit: $limit) {
      tickId
      status
    }
    runsCount
    runs(limit: 10) {
      runId
      tags {
        key
        value
      }
      pipeline {
        name
      }
      status
    }
    stats {
      ticksStarted
      ticksSucceeded
      ticksSkipped
      ticksFailed
    }
    ticksCount
    status
  }
`;

const ScheduleName = styled.pre`
  margin: 0;
`;

const Stat = styled.div`
  text-align: center;
  padding: 2px;
  font-size: 10px;
`;

const StatNumber = styled.div`
  font-size: 15px;
  font-weight: bold;
`;

const ErrorTag = styled.div`
  display: block;
  margin-top: 8px;
`;

const START_SCHEDULE_MUTATION = gql`
  mutation StartSchedule($scheduleName: String!) {
    startSchedule(scheduleName: $scheduleName) {
      __typename
      ... on RunningScheduleResult {
        schedule {
          __typename
          runningScheduleCount
          scheduleDefinition {
            __typename
            name
          }
          status
        }
      }
      ... on PythonError {
        message
        stack
      }
    }
  }
`;

const STOP_SCHEDULE_MUTATION = gql`
  mutation StopSchedule($scheduleName: String!) {
    stopRunningSchedule(scheduleName: $scheduleName) {
      __typename
      ... on RunningScheduleResult {
        schedule {
          __typename
          runningScheduleCount
          scheduleDefinition {
            __typename
            name
          }
          status
        }
      }
      ... on PythonError {
        message
        stack
      }
    }
  }
`;
