import * as React from "react";
import * as qs from "query-string";
import { useMutation, useQuery } from "@apollo/react-hooks";

import {
  Switch,
  Button,
  Icon,
  Menu,
  MenuItem,
  MenuDivider,
  Popover,
  Tooltip,
  Tag,
  Intent,
  PopoverInteractionKind,
  Position,
  Spinner
} from "@blueprintjs/core";
import { HighlightedCodeBlock } from "../HighlightedCodeBlock";
import { RowColumn, RowContainer } from "../ListComponents";
import { ScheduleDefinitionFragment } from "./types/ScheduleDefinitionFragment";
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
import { useScheduleSelector } from "../DagsterRepositoryContext";
import { ScheduleStateFragment } from "./types/ScheduleStateFragment";

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
      "Schedule is set to be running, but either the scheduler is not configured or the scheduler is not running the schedule"
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

const displayScheduleMutationErrors = (data: StartSchedule | StopSchedule) => {
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

export const ScheduleRow: React.FunctionComponent<{
  schedule: ScheduleDefinitionFragment;
}> = ({ schedule }) => {
  const match = useRouteMatch("/schedules/:scheduleName");

  const [startSchedule, { loading: toggleOnInFlight }] = useMutation(
    START_SCHEDULE_MUTATION,
    {
      onCompleted: displayScheduleMutationErrors
    }
  );
  const [stopSchedule, { loading: toggleOffInFlight }] = useMutation(
    STOP_SCHEDULE_MUTATION,
    {
      onCompleted: displayScheduleMutationErrors
    }
  );

  const {
    name,
    cronSchedule,
    pipelineName,
    mode,
    solidSelection,
    scheduleState
  } = schedule;

  const scheduleSelector = useScheduleSelector(name);

  const [configRequested, setConfigRequested] = React.useState(false);

  const { data, loading: yamlLoading } = useQuery(FETCH_SCHEDULE_YAML, {
    variables: { scheduleSelector },
    skip: !configRequested
  });
  const runConfigYaml = data?.scheduleDefinitionOrError?.runConfigYaml;

  const displayName = match ? (
    <ScheduleName>{name}</ScheduleName>
  ) : (
    <Link to={`/schedules/${name}`}>
      <ScheduleName>{name}</ScheduleName>
    </Link>
  );

  if (!scheduleState) {
    return (
      <RowContainer key={name}>
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
        </RowColumn>
      </RowContainer>
    );
  }

  const {
    status,
    runningScheduleCount,
    stats,
    ticks,
    runs,
    runsCount
  } = scheduleState;

  const latestTick = ticks.length > 0 ? ticks[0] : null;

  return (
    <RowContainer key={name}>
      <RowColumn style={{ maxWidth: 60, paddingLeft: 0, textAlign: "center" }}>
        <Switch
          checked={status === ScheduleStatus.RUNNING}
          large={true}
          disabled={toggleOffInFlight || toggleOnInFlight}
          innerLabelChecked="on"
          innerLabel="off"
          onChange={() => {
            if (status === ScheduleStatus.RUNNING) {
              stopSchedule({
                variables: { scheduleSelector }
              });
            } else {
              startSchedule({
                variables: { scheduleSelector }
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
                <Link to={`/runs/${run.pipelineName}/${run.runId}`}>
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
            yamlLoading ? (
              <Spinner size={32} />
            ) : (
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
                <MenuItem
                  text="Open in Playground..."
                  icon="edit"
                  target="_blank"
                  disabled={!runConfigYaml}
                  href={`/pipeline/${pipelineName}/playground/setup?${qs.stringify(
                    {
                      mode,
                      solidSelection,
                      config: runConfigYaml
                    }
                  )}`}
                />
                <MenuDivider />
              </Menu>
            )
          }
          position={"bottom"}
        >
          <Button
            minimal={true}
            icon="chevron-down"
            onClick={() => {
              setConfigRequested(true);
            }}
          />
        </Popover>
      </RowColumn>
    </RowContainer>
  );
};

export const ScheduleStateRow: React.FunctionComponent<{
  scheduleState: ScheduleStateFragment;
}> = ({ scheduleState }) => {
  const {
    scheduleName,
    cronSchedule,
    stats,
    ticks,
    runs,
    runsCount
  } = scheduleState;

  const latestTick = ticks.length > 0 ? ticks[0] : null;

  return (
    <RowContainer key={scheduleName}>
      <RowColumn style={{ flex: 1.4 }}>
        <div>{scheduleName}</div>
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
                <Link to={`/runs/${run.pipelineName}/${run.runId}`}>
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
                `tag:dagster/schedule_name=${scheduleName}`
              )}`}
              style={{ verticalAlign: "top" }}
            >
              {" "}
              +{runsCount - NUM_RUNS_TO_DISPLAY} more
            </Link>
          )}
        </div>
      </RowColumn>
    </RowContainer>
  );
};

export const ScheduleFragment = gql`
  fragment ScheduleStateFragment on ScheduleState {
    __typename
    id
    scheduleOriginId
    scheduleName
    cronSchedule
    runningScheduleCount
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
      pipelineName
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

  fragment ScheduleDefinitionFragment on ScheduleDefinition {
    name
    cronSchedule
    pipelineName
    solidSelection
    mode
    partitionSet {
      name
    }
    scheduleState {
      ...ScheduleStateFragment
    }
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

const FETCH_SCHEDULE_YAML = gql`
  query FetchScheduleYaml($scheduleSelector: ScheduleSelector!) {
    scheduleDefinitionOrError(scheduleSelector: $scheduleSelector) {
      ... on ScheduleDefinition {
        runConfigYaml
      }
    }
  }
`;

const START_SCHEDULE_MUTATION = gql`
  mutation StartSchedule($scheduleSelector: ScheduleSelector!) {
    startSchedule(scheduleSelector: $scheduleSelector) {
      __typename
      ... on ScheduleStateResult {
        scheduleState {
          __typename
          id
          runningScheduleCount
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
  mutation StopSchedule($scheduleSelector: ScheduleSelector!) {
    stopRunningSchedule(scheduleSelector: $scheduleSelector) {
      __typename
      ... on ScheduleStateResult {
        scheduleState {
          __typename
          id
          runningScheduleCount
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
