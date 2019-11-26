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
  Tooltip,
  Tag,
  Intent
} from "@blueprintjs/core";
import { HighlightedCodeBlock } from "../HighlightedCodeBlock";
import { RowColumn, RowContainer } from "../ListComponents";
import { RunStatus, titleForRun } from "../runs/RunUtils";
import {
  ScheduleFragment,
  ScheduleFragment_runs
} from "./types/ScheduleFragment";
import { ScheduleStatus, ScheduleAttemptStatus } from "../types/globalTypes";
import { Link } from "react-router-dom";
import cronstrue from "cronstrue";
import gql from "graphql-tag";
import { showCustomAlert } from "../CustomAlertProvider";
import styled from "styled-components";
import { copyValue, unixTimestampToString } from "../Util";

const NUM_RUNS_TO_DISPLAY = 10;

const ScheduleRow: React.FunctionComponent<{
  schedule: ScheduleFragment;
}> = ({ schedule }) => {
  const {
    id,
    status,
    scheduleDefinition,
    runs,
    runsCount,
    logsPath,
    attempts
  } = schedule;
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

  const mostRecentAttempt = attempts.length > 0 ? attempts[0] : null;
  const mostRecentAttemptLogError = mostRecentAttempt
    ? JSON.parse(mostRecentAttempt.jsonResult)
    : null;

  const getNaturalLanguageCronString = (cronSchedule: string) => {
    try {
      return cronstrue.toString(cronSchedule);
    } catch {
      return "Invalid cron string";
    }
  };

  const sortRuns = (runs: ScheduleFragment_runs[]) => {
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
                      id: id,
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
                      id: id,
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
      <RowColumn style={{ flex: 1.4 }}>
        <ScheduleName>{name}</ScheduleName>
      </RowColumn>
      <RowColumn>
        <Link to={`/p/${pipelineName}/explore/`}>
          <Icon icon="diagram-tree" /> {pipelineName}
        </Link>
      </RowColumn>
      <RowColumn
        style={{
          maxWidth: 150
        }}
      >
        {cronSchedule ? (
          <Tooltip
            className={Classes.TOOLTIP_INDICATOR}
            position={"top"}
            content={cronSchedule}
          >
            {getNaturalLanguageCronString(cronSchedule)}
          </Tooltip>
        ) : (
          "-"
        )}
      </RowColumn>
      <RowColumn style={{ flex: 1 }}>
        {runs && runs.length > 0
          ? runs.slice(0, NUM_RUNS_TO_DISPLAY).map(run => (
              <div
                style={{
                  display: "inline-block",
                  cursor: "pointer",
                  marginRight: 5
                }}
                key={run.runId}
              >
                <Link to={`/p/${run.pipeline.name}/runs/${run.runId}`}>
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
            ))
          : "-"}
        {runsCount > NUM_RUNS_TO_DISPLAY && (
          <Link
            to={`/runs?q=tag:${encodeURIComponent(
              "dagster/schedule_id"
            )}=${id}`}
            style={{ verticalAlign: "top" }}
          >
            {" "}
            +{runsCount - NUM_RUNS_TO_DISPLAY} more
          </Link>
        )}
      </RowColumn>
      <RowColumn style={{ flex: 1 }}>
        {mostRecentRun
          ? unixTimestampToString(mostRecentRun.stats.startTime)
          : "No previous runs"}

        {mostRecentAttempt &&
          mostRecentAttempt.status === ScheduleAttemptStatus.ERROR && (
            <ErrorTag>
              <Tag intent={Intent.WARNING}>
                Latest run failed:
                <ErrorLink
                  onClick={() =>
                    showCustomAlert({
                      title: "Error",
                      body: (
                        <>
                          <ErrorHeader>
                            {mostRecentAttemptLogError.__typename}
                          </ErrorHeader>
                          <ErrorWrapper>
                            <HighlightedCodeBlock
                              value={JSON.stringify(
                                mostRecentAttemptLogError,
                                null,
                                2
                              )}
                              languages={["json"]}
                            />
                          </ErrorWrapper>
                        </>
                      )
                    })
                  }
                >
                  View Error
                </ErrorLink>
              </Tag>
            </ErrorTag>
          )}
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
                        value={environmentConfigYaml}
                        languages={["yaml"]}
                      />
                    )
                  })
                }
              />
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
    id
    scheduleDefinition {
      name
      executionParamsString
      environmentConfigYaml
      cronSchedule
    }
    logsPath
    runsCount
    attempts(limit: 1) {
      time
      jsonResult
      status
    }
    runs(limit: $limit) {
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
`;

const ScheduleName = styled.pre`
  margin: 0;
`;

const ErrorHeader = styled.h3`
  color: #b05c47;
  font-weight: 400;
  margin: 0.5em 0 0.25em;
`;

const ErrorWrapper = styled.pre`
  background-color: rgba(206, 17, 38, 0.05);
  border: 1px solid #d17257;
  border-radius: 3px;
  max-width: 90vw;
  padding: 1em 2em;
`;

const ErrorTag = styled.div`
  display: block;
  margin-top: 5px;
`;

const ErrorLink = styled.a`
  color: white;
  text-decoration: underline;
  margin-left: 10px;
`;

const START_SCHEDULE_MUTATION = gql`
  mutation StartSchedule($scheduleName: String!) {
    startSchedule(scheduleName: $scheduleName) {
      schedule {
        id
        status
      }
    }
  }
`;

const STOP_SCHEDULE_MUTATION = gql`
  mutation StopSchedule($scheduleName: String!) {
    stopRunningSchedule(scheduleName: $scheduleName) {
      schedule {
        id
        status
      }
    }
  }
`;

export default ScheduleRow;
