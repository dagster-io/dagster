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
  Spinner,
  Code
} from "@blueprintjs/core";
import { HighlightedCodeBlock } from "../HighlightedCodeBlock";
import { RowColumn, RowContainer } from "../ListComponents";
import {
  ScheduleDefinitionFragment,
  ScheduleDefinitionFragment_scheduleState_ticks_tickSpecificData
} from "./types/ScheduleDefinitionFragment";
import { StartSchedule, StartSchedule_startSchedule_PythonError } from "./types/StartSchedule";
import { StopSchedule, StopSchedule_stopRunningSchedule_PythonError } from "./types/StopSchedule";
import { ScheduleStatus, ScheduleTickStatus } from "../types/globalTypes";
import { Legend, LegendColumn } from "../ListComponents";

import { Link, useRouteMatch, useHistory } from "react-router-dom";
import cronstrue from "cronstrue";
import gql from "graphql-tag";
import { showCustomAlert } from "../CustomAlertProvider";
import styled from "styled-components/macro";
import { titleForRun } from "../runs/RunUtils";
import { RunStatus } from "../runs/RunStatusDots";
import PythonErrorInfo from "../PythonErrorInfo";
import {
  useScheduleSelector,
  scheduleSelectorWithRepository,
  DagsterRepoOption,
  useRepositoryOptions,
  useCurrentRepositoryState,
  repositorySelectorFromDagsterRepoOption
} from "../DagsterRepositoryContext";
import { ScheduleStateFragment } from "./types/ScheduleStateFragment";
import { assertUnreachable } from "../Util";
import { ReconcileButton } from "./ReconcileButton";

type TickSpecificData = ScheduleDefinitionFragment_scheduleState_ticks_tickSpecificData | null;

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
    errors.push("Schedule is set to be stopped, but the scheduler is still running the schedule");
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

        <p>Errors:</p>
        <ul>
          {errors.map((error, index) => (
            <li key={index}>{error}</li>
          ))}
        </ul>

        <p>
          To resolve, click <ReconcileButton /> or run <Code>dagster schedule up</Code>
        </p>
      </div>
    </Popover>
  );
};

const displayScheduleMutationErrors = (data: StartSchedule | StopSchedule) => {
  let error:
    | StartSchedule_startSchedule_PythonError
    | StopSchedule_stopRunningSchedule_PythonError
    | null = null;

  if ("startSchedule" in data && data.startSchedule.__typename === "PythonError") {
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

  const [startSchedule, { loading: toggleOnInFlight }] = useMutation(START_SCHEDULE_MUTATION, {
    onCompleted: displayScheduleMutationErrors
  });
  const [stopSchedule, { loading: toggleOffInFlight }] = useMutation(STOP_SCHEDULE_MUTATION, {
    onCompleted: displayScheduleMutationErrors
  });

  const { name, cronSchedule, pipelineName, mode, solidSelection, scheduleState } = schedule;

  const scheduleId = scheduleState?.scheduleOriginId;

  const scheduleSelector = useScheduleSelector(name);

  const [configRequested, setConfigRequested] = React.useState(false);

  const { data, loading: yamlLoading } = useQuery(FETCH_SCHEDULE_YAML, {
    variables: { scheduleSelector },
    skip: !configRequested
  });

  const runConfigError =
    data?.scheduleDefinitionOrError?.runConfigOrError.__typename === "PythonError"
      ? data.scheduleDefinitionOrError.runConfigOrError
      : null;

  const runConfigYaml = runConfigError
    ? null
    : data?.scheduleDefinitionOrError?.runConfigOrError.yaml;

  const displayName = match ? (
    <ScheduleName>{name}</ScheduleName>
  ) : (
    <>
      <Link to={`/schedules/${name}`}>
        <ScheduleName>{name}</ScheduleName>
      </Link>

      {scheduleId && <span style={{ fontSize: 10 }}>Schedule ID: {scheduleId}</span>}
    </>
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

  const { status, runningScheduleCount, ticks, runs, runsCount, scheduleOriginId } = scheduleState;

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
                variables: { scheduleOriginId }
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
      <RowColumn style={{ maxWidth: 100 }}>
        {latestTick ? (
          <TickTag status={latestTick.status} eventSpecificData={latestTick.tickSpecificData} />
        ) : null}
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
            const [partition] = run.tags
              .filter(tag => tag.key === "dagster/partition")
              .map(tag => tag.value);
            const runLabel = partition ? (
              <>
                <div>Run id: {titleForRun(run)}</div>
                <div>Partition: {partition}</div>
              </>
            ) : (
              titleForRun(run)
            );
            return (
              <div
                style={{
                  display: "inline-block",
                  cursor: "pointer",
                  marginRight: 5
                }}
                key={run.runId}
              >
                <Link to={`/pipeline/${run.pipelineName}/runs/${run.runId}`}>
                  <Tooltip
                    position={"top"}
                    content={runLabel}
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
              to={`/runs/?q=${encodeURIComponent(`tag:dagster/schedule_name=${name}`)}`}
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
                  onClick={() => {
                    if (runConfigError) {
                      showCustomAlert({
                        body: <PythonErrorInfo error={runConfigError} />
                      });
                    } else {
                      showCustomAlert({
                        title: "Config",
                        body: (
                          <HighlightedCodeBlock
                            value={runConfigYaml || "Unable to resolve config"}
                            languages={["yaml"]}
                          />
                        )
                      });
                    }
                  }}
                />
                <MenuItem
                  text="Open in Playground..."
                  icon="edit"
                  target="_blank"
                  disabled={!runConfigYaml}
                  href={`/pipeline/${pipelineName}/playground/setup?${qs.stringify({
                    mode,
                    solidSelection,
                    config: runConfigYaml
                  })}`}
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

export const ScheduleRowHeader: React.FunctionComponent<{
  schedule: ScheduleDefinitionFragment;
}> = ({ schedule }) => {
  if (!schedule.scheduleState) {
    return (
      <Legend>
        <LegendColumn style={{ flex: 1.4 }}>Schedule Name</LegendColumn>
        <LegendColumn>Pipeline</LegendColumn>
        <LegendColumn style={{ maxWidth: 150 }}>Schedule</LegendColumn>
        <LegendColumn style={{ flex: 1 }}>Execution Params</LegendColumn>
      </Legend>
    );
  } else {
    return (
      <Legend>
        <LegendColumn style={{ maxWidth: 60 }}></LegendColumn>
        <LegendColumn style={{ flex: 1.4 }}>Schedule Name</LegendColumn>
        <LegendColumn>Pipeline</LegendColumn>
        <LegendColumn style={{ maxWidth: 150 }}>Schedule</LegendColumn>
        <LegendColumn style={{ maxWidth: 100 }}>Last Tick</LegendColumn>
        <LegendColumn style={{ flex: 1 }}>Latest Runs</LegendColumn>
        <LegendColumn style={{ flex: 1 }}>Execution Params</LegendColumn>
      </Legend>
    );
  }
};

export const ScheduleStateRow: React.FunctionComponent<{
  scheduleState: ScheduleStateFragment;
  showStatus?: boolean;
  dagsterRepoOption?: DagsterRepoOption;
}> = ({ scheduleState, showStatus = false, dagsterRepoOption }) => {
  const [startSchedule, { loading: toggleOnInFlight }] = useMutation(START_SCHEDULE_MUTATION, {
    onCompleted: displayScheduleMutationErrors
  });
  const [stopSchedule, { loading: toggleOffInFlight }] = useMutation(STOP_SCHEDULE_MUTATION, {
    onCompleted: displayScheduleMutationErrors
  });

  const { options } = useRepositoryOptions();
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_, setRepo] = useCurrentRepositoryState(options);
  const history = useHistory();

  const {
    status,
    scheduleName,
    cronSchedule,
    ticks,
    runs,
    runsCount,
    scheduleOriginId
  } = scheduleState;
  const latestTick = ticks.length > 0 ? ticks[0] : null;

  const goToRepositorySchedules = () => {
    if (!dagsterRepoOption) return;
    setRepo(dagsterRepoOption);
    history.push(`/schedules`);
  };

  const goToSchedule = () => {
    if (!dagsterRepoOption) return;
    setRepo(dagsterRepoOption);
    history.push(`/schedules/${scheduleName}`);
  };

  return (
    <RowContainer key={scheduleName}>
      {showStatus && (
        <RowColumn style={{ maxWidth: 60, paddingLeft: 0, textAlign: "center" }}>
          <Switch
            checked={status === ScheduleStatus.RUNNING}
            large={true}
            disabled={!dagsterRepoOption || toggleOffInFlight || toggleOnInFlight}
            innerLabelChecked="on"
            innerLabel="off"
            onChange={() => {
              if (!dagsterRepoOption) {
                return;
              }

              const scheduleSelector = scheduleSelectorWithRepository(
                scheduleName,
                repositorySelectorFromDagsterRepoOption(dagsterRepoOption)
              );

              if (status === ScheduleStatus.RUNNING) {
                stopSchedule({
                  variables: { scheduleOriginId }
                });
              } else {
                startSchedule({
                  variables: { scheduleSelector }
                });
              }
            }}
          />
        </RowColumn>
      )}
      <RowColumn style={{ flex: 1.4 }}>
        <div>{scheduleName}</div>
        {dagsterRepoOption && (
          <div style={{ marginTop: 10 }}>
            <Button onClick={goToRepositorySchedules} small={true}>
              Go to repository schedules
            </Button>{" "}
            <Button onClick={goToSchedule} small={true}>
              Go to schedule page
            </Button>
          </div>
        )}
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
      <RowColumn style={{ flex: 1 }}>
        {latestTick ? (
          <TickTag status={latestTick.status} eventSpecificData={latestTick.tickSpecificData} />
        ) : null}
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
                <Link to={`/pipeline/${run.pipelineName}/runs/${run.runId}`}>
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
              to={`/runs/?q=${encodeURIComponent(`tag:dagster/schedule_name=${scheduleName}`)}`}
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

export const TickTag: React.FunctionComponent<{
  status: ScheduleTickStatus;
  eventSpecificData: TickSpecificData;
}> = ({ status, eventSpecificData }) => {
  switch (status) {
    case ScheduleTickStatus.STARTED:
      return (
        <Tag minimal={true} intent={Intent.PRIMARY}>
          Started
        </Tag>
      );
    case ScheduleTickStatus.SUCCESS:
      if (!eventSpecificData || eventSpecificData.__typename !== "ScheduleTickSuccessData") {
        return (
          <Tag minimal={true} intent={Intent.SUCCESS}>
            Success
          </Tag>
        );
      } else {
        return (
          <a
            href={`/pipeline/${eventSpecificData.run?.pipelineName}/runs/${eventSpecificData.run?.runId}`}
            style={{ textDecoration: "none" }}
          >
            <Tag minimal={true} intent={Intent.SUCCESS} interactive={true}>
              Success
            </Tag>
          </a>
        );
      }
    case ScheduleTickStatus.SKIPPED:
      return (
        <Tag minimal={true} intent={Intent.WARNING}>
          Skipped
        </Tag>
      );
    case ScheduleTickStatus.FAILURE:
      if (!eventSpecificData || eventSpecificData.__typename !== "ScheduleTickFailureData") {
        return (
          <Tag minimal={true} intent={Intent.DANGER}>
            Failure
          </Tag>
        );
      } else {
        return (
          <LinkButton
            onClick={() =>
              showCustomAlert({
                title: "Schedule Response",
                body: <PythonErrorInfo error={eventSpecificData.error} />
              })
            }
          >
            <Tag minimal={true} intent={Intent.DANGER} interactive={true}>
              Failure
            </Tag>
          </LinkButton>
        );
      }
    default:
      return assertUnreachable(status);
  }
};

const ScheduleName = styled.pre`
  margin: 0;
`;

const FETCH_SCHEDULE_YAML = gql`
  query FetchScheduleYaml($scheduleSelector: ScheduleSelector!) {
    scheduleDefinitionOrError(scheduleSelector: $scheduleSelector) {
      ... on ScheduleDefinition {
        runConfigOrError {
          ... on ScheduleRunConfig {
            yaml
          }
          ... on PythonError {
            ...PythonErrorFragment
          }
        }
      }
    }
  }
  ${PythonErrorInfo.fragments.PythonErrorFragment}
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
  mutation StopSchedule($scheduleOriginId: String!) {
    stopRunningSchedule(scheduleOriginId: $scheduleOriginId) {
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

const LinkButton = styled.button`
  background: inherit;
  border: none;
  cursor: pointer;
  font-size: inherit;
  text-decoration: none;
  padding: 0;
`;
