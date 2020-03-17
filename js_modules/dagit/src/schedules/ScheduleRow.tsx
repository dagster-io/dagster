import * as React from "react";
import * as qs from "query-string";
import { useMutation } from "@apollo/react-hooks";

import {
  Button,
  Colors,
  Switch,
  Icon,
  Menu,
  MenuItem,
  MenuDivider,
  Popover,
  Tooltip,
  Tag,
  Intent
} from "@blueprintjs/core";
import { HighlightedCodeBlock } from "../HighlightedCodeBlock";
import { RowColumn, RowContainer } from "../ListComponents";
import { ScheduleFragment } from "./types/ScheduleFragment";
import {
  ScheduleStatus,
  ScheduleTickStatus,
  ScheduleAttemptStatus
} from "../types/globalTypes";

import { Link, useRouteMatch } from "react-router-dom";
import cronstrue from "cronstrue";
import gql from "graphql-tag";
import { showCustomAlert } from "../CustomAlertProvider";
import styled from "styled-components/macro";
import { copyValue } from "../DomUtils";
import { titleForRun, RunStatus } from "../runs/RunUtils";

const NUM_RUNS_TO_DISPLAY = 10;

const getNaturalLanguageCronString = (cronSchedule: string) => {
  try {
    return cronstrue.toString(cronSchedule);
  } catch {
    return "Invalid cron string";
  }
};

export const ScheduleRow: React.FunctionComponent<{
  schedule: ScheduleFragment;
}> = ({ schedule }) => {
  const {
    status,
    scheduleDefinition,
    logsPath,
    stats,
    ticks,
    runs,
    runsCount
  } = schedule;
  const {
    name,
    cronSchedule,
    pipelineName,
    solidSubset,
    mode,
    environmentConfigYaml
  } = scheduleDefinition;

  const [startSchedule] = useMutation(START_SCHEDULE_MUTATION);
  const [stopSchedule] = useMutation(STOP_SCHEDULE_MUTATION);
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
                variables: { scheduleName: name },
                optimisticResponse: {
                  stopRunningSchedule: {
                    __typename: "RunningScheduleResult",
                    schedule: {
                      scheduleDefinition: {
                        __typename: "ScheduleDefinition",
                        name: name
                      },
                      __typename: "RunningSchedule",
                      status: ScheduleStatus.STOPPED
                    }
                  }
                }
              });
            } else {
              startSchedule({
                variables: { scheduleName: name },
                optimisticResponse: {
                  startSchedule: {
                    __typename: "RunningScheduleResult",
                    schedule: {
                      scheduleDefinition: {
                        __typename: "ScheduleDefinition",
                        name: name
                      },
                      __typename: "RunningSchedule",
                      status: ScheduleStatus.RUNNING
                    }
                  }
                }
              });
            }
          }}
        />
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
                        value={
                          environmentConfigYaml || "Unable to resolve config"
                        }
                        languages={["yaml"]}
                      />
                    )
                  })
                }
              />
              {environmentConfigYaml !== null ? (
                <MenuItem
                  text="Open in Execute Tab..."
                  icon="edit"
                  target="_blank"
                  href={`/playground/${pipelineName}/setup?${qs.stringify({
                    mode,
                    solidSubset,
                    config: environmentConfigYaml
                  })}`}
                />
              ) : (
                <MenuItem
                  text="Open in Execute Tab..."
                  icon="edit"
                  disabled={true}
                />
              )}
              <MenuDivider />
              <MenuItem
                text="Copy Path to Debug Logs"
                icon="clipboard"
                onClick={(e: React.MouseEvent<any>) => copyValue(e, logsPath)}
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

export const ScheduleRowFragment = gql`
  fragment ScheduleFragment on RunningSchedule {
    __typename
    scheduleDefinition {
      name
      cronSchedule
      pipelineName
      solidSubset
      mode
      environmentConfigYaml
    }
    logsPath
    ticks(limit: $limit) {
      tickId
      status
    }
    runsCount
    runs(limit: 10) {
      runId
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
      schedule {
        __typename
        scheduleDefinition {
          __typename
          name
        }
        status
      }
    }
  }
`;

const STOP_SCHEDULE_MUTATION = gql`
  mutation StopSchedule($scheduleName: String!) {
    stopRunningSchedule(scheduleName: $scheduleName) {
      schedule {
        __typename
        scheduleDefinition {
          __typename
          name
        }
        status
      }
    }
  }
`;

export const AttemptStatus = styled.div<{ status: ScheduleAttemptStatus }>`
  display: inline-block;
  width: 11px;
  height: 11px;
  border-radius: 5.5px;
  align-self: center;
  transition: background 200ms linear;
  background: ${({ status }) =>
    ({
      [ScheduleAttemptStatus.SUCCESS]: Colors.GREEN2,
      [ScheduleAttemptStatus.ERROR]: Colors.RED3,
      [ScheduleAttemptStatus.SKIPPED]: Colors.GOLD3
    }[status])};
  &:hover {
    background: ${({ status }) =>
      ({
        [ScheduleAttemptStatus.SUCCESS]: Colors.GREEN2,
        [ScheduleAttemptStatus.ERROR]: Colors.RED3,
        [ScheduleAttemptStatus.SKIPPED]: Colors.GOLD3
      }[status])};
  }
`;
