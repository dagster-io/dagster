import * as React from "react";
import * as qs from "query-string";
import * as yaml from "yaml";
import gql from "graphql-tag";
import {
  Button,
  Colors,
  Icon,
  Menu,
  MenuItem,
  Popover,
  MenuDivider,
  Tooltip,
  NonIdealState,
  Tag,
  Intent
} from "@blueprintjs/core";
import {
  Details,
  Legend,
  LegendColumn,
  RowColumn,
  RowContainer
} from "../ListComponents";
import {
  RunStatus,
  titleForRun,
  handleStartExecutionResult,
  REEXECUTE_MUTATION,
  DELETE_MUTATION,
  CANCEL_MUTATION
} from "./RunUtils";
import { formatElapsedTime, unixTimestampToString } from "../Util";
import { SharedToaster } from "../DomUtils";

import { HighlightedCodeBlock } from "../HighlightedCodeBlock";
import { Link } from "react-router-dom";
import { RunTableRunFragment } from "./types/RunTableRunFragment";
import { showCustomAlert } from "../CustomAlertProvider";
import { useMutation } from "react-apollo";
import { RUNS_ROOT_QUERY, RunsQueryVariablesContext } from "./RunsRoot";
import PythonErrorInfo from "../PythonErrorInfo";

interface RunTableProps {
  runs: RunTableRunFragment[];
}

const TOOLTIP_MESSAGE_PIPELINE_MISSING =
  `This pipeline is not present in the currently loaded repository, ` +
  `so dagit can't browse the pipeline solids, but you can still view the logs.`;

export class RunTable extends React.Component<RunTableProps> {
  static fragments = {
    RunTableRunFragment: gql`
      fragment RunTableRunFragment on PipelineRun {
        runId
        status
        stepKeysToExecute
        canCancel
        mode
        environmentConfigYaml
        pipeline {
          __typename

          ... on PipelineReference {
            name
          }
          ... on Pipeline {
            solids {
              name
            }
          }
        }
        stats {
          __typename
          ... on PipelineRunStatsSnapshot {
            stepsSucceeded
            stepsFailed
            startTime
            endTime
            expectations
            materializations
          }
          ... on PythonError {
            message
            stack
          }
        }
        tags {
          key
          value
        }
      }
    `
  };

  render() {
    if (this.props.runs.length === 0) {
      return (
        <div style={{ marginTop: 100 }}>
          <NonIdealState
            icon="history"
            title="Pipeline Runs"
            description="No runs to display. Use the Execute tab to start a pipeline."
          />
        </div>
      );
    }
    return (
      <div>
        <Legend>
          <LegendColumn style={{ maxWidth: 30 }}></LegendColumn>
          <LegendColumn style={{ flex: 2.4 }}>Run</LegendColumn>
          <LegendColumn>Pipeline</LegendColumn>
          <LegendColumn style={{ flex: 1 }}>Execution Params</LegendColumn>
          <LegendColumn style={{ flex: 1.8 }}>Timing</LegendColumn>
          <LegendColumn style={{ maxWidth: 50 }}></LegendColumn>
        </Legend>
        {this.props.runs.map(run => (
          <RunRow run={run} key={run.runId} />
        ))}
      </div>
    );
  }
}

const RunRow: React.FunctionComponent<{ run: RunTableRunFragment }> = ({
  run
}) => {
  let details;
  let time;
  if (run.stats.__typename === "PipelineRunStatsSnapshot") {
    details = (
      <Details>
        <Link
          to={`/p/${run.pipeline.name}/runs/${run.runId}?q=type:step_success`}
        >{`${run.stats.stepsSucceeded} steps succeeded, `}</Link>
        <Link
          to={`/p/${run.pipeline.name}/runs/${run.runId}?q=type:step_failure`}
        >
          {`${run.stats.stepsFailed} steps failed, `}{" "}
        </Link>
        <Link
          to={`/p/${run.pipeline.name}/runs/${run.runId}?q=type:materialization`}
        >{`${run.stats.materializations} materializations`}</Link>
        ,{" "}
        <Link
          to={`/p/${run.pipeline.name}/runs/${run.runId}?q=type:expectation`}
        >{`${run.stats.expectations} expectations passed`}</Link>
      </Details>
    );
    time = (
      <>
        {run.stats.startTime ? (
          <div style={{ marginBottom: 4 }}>
            <Icon icon="calendar" />{" "}
            {unixTimestampToString(run.stats.startTime)}
            <Icon
              icon="arrow-right"
              style={{ marginLeft: 10, marginRight: 10 }}
            />
            {unixTimestampToString(run.stats.endTime)}
          </div>
        ) : run.status === "FAILURE" ? (
          <div style={{ marginBottom: 4 }}> Failed to start</div>
        ) : (
          <div style={{ marginBottom: 4 }}>
            <Icon icon="calendar" /> Starting...
          </div>
        )}
        <RunTime startUnix={run.stats.startTime} endUnix={run.stats.endTime} />
      </>
    );
  } else {
    details = (
      <Popover
        content={<PythonErrorInfo error={run.stats} />}
        targetTagName="div"
      >
        <Details>
          <Icon icon="error" /> Failed to load stats
        </Details>
      </Popover>
    );
    time = (
      <Popover content={<PythonErrorInfo error={run.stats} />}>
        <div>
          <Icon icon="error" /> Failed to load times
        </div>
      </Popover>
    );
  }

  return (
    <RowContainer key={run.runId} style={{ paddingRight: 3 }}>
      <RowColumn style={{ maxWidth: 30, paddingLeft: 0, textAlign: "center" }}>
        <RunStatus status={run.status} />
      </RowColumn>
      <RowColumn style={{ flex: 2.4 }}>
        <Link to={`/p/${run.pipeline.name}/runs/${run.runId}`}>
          {titleForRun(run)}
        </Link>
        {details}
      </RowColumn>
      <RowColumn>
        {run.pipeline.__typename === "Pipeline" ? (
          <Link to={`/p/${run.pipeline.name}/explore/`}>
            <Icon icon="diagram-tree" /> {run.pipeline.name}
          </Link>
        ) : (
          <>
            <Icon icon="diagram-tree" color={Colors.GRAY3} />
            &nbsp;
            <Tooltip content={TOOLTIP_MESSAGE_PIPELINE_MISSING}>
              {run.pipeline.name}
            </Tooltip>
          </>
        )}
      </RowColumn>
      <RowColumn>
        <div>
          <div>{`Mode: ${run.mode}`}</div>

          {run.stepKeysToExecute && (
            <div>
              {run.stepKeysToExecute.length === 1
                ? `Step: ${run.stepKeysToExecute.join("")}`
                : `${run.stepKeysToExecute.length} Steps`}
            </div>
          )}
          <div>
            {run.tags.map((t, idx) => {
              // Manually hide 'dagster/schedule_id` tags
              if (t.key === "dagster/schedule_id") {
                return null;
              }

              return (
                <Tooltip
                  content={`${t.key}=${t.value}`}
                  key={idx}
                  wrapperTagName="div"
                  targetTagName="div"
                >
                  <Tag style={{ margin: 1 }}>{`${t.key}=${t.value}`}</Tag>
                </Tooltip>
              );
            })}
          </div>
        </div>
      </RowColumn>
      <RowColumn style={{ flex: 1.8, borderRight: 0 }}>{time}</RowColumn>
      <RowColumn style={{ maxWidth: 50 }}>
        <RunActionsMenu run={run} />
      </RowColumn>
    </RowContainer>
  );
};

const RunActionsMenu: React.FunctionComponent<{
  run: RunTableRunFragment;
}> = ({ run }) => {
  const variables = React.useContext(RunsQueryVariablesContext);
  const [reexecute] = useMutation(REEXECUTE_MUTATION);
  const [cancel] = useMutation(CANCEL_MUTATION, {
    refetchQueries: [{ query: RUNS_ROOT_QUERY, variables }]
  });
  const [destroy] = useMutation(DELETE_MUTATION, {
    refetchQueries: [{ query: RUNS_ROOT_QUERY, variables }]
  });

  return (
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
                    value={run.environmentConfigYaml}
                    languages={["yaml"]}
                  />
                )
              })
            }
          />
          <MenuDivider />

          <MenuItem
            text="Open in Execute Tab..."
            disabled={run.pipeline.__typename !== "Pipeline"}
            icon="edit"
            target="_blank"
            href={`/p/${run.pipeline.name}/execute/setup?${qs.stringify({
              mode: run.mode,
              config: run.environmentConfigYaml,
              solidSubset:
                run.pipeline.__typename === "Pipeline"
                  ? run.pipeline.solids.map(s => s.name)
                  : []
            })}`}
          />
          <MenuItem
            text="Re-execute"
            disabled={run.pipeline.__typename !== "Pipeline"}
            icon="repeat"
            onClick={async () => {
              const result = await reexecute({
                variables: {
                  executionParams: {
                    mode: run.mode,
                    environmentConfigData: yaml.parse(
                      run.environmentConfigYaml
                    ),
                    selector: {
                      name: run.pipeline.name,
                      solidSubset:
                        run.pipeline.__typename === "Pipeline"
                          ? run.pipeline.solids.map(s => s.name)
                          : []
                    }
                  }
                }
              });
              handleStartExecutionResult(run.pipeline.name, result, {
                openInNewWindow: false
              });
            }}
          />
          <MenuItem
            text="Cancel"
            icon="stop"
            disabled={!run.canCancel}
            onClick={async () => {
              const result = await cancel({ variables: { runId: run.runId } });
              showToastFor(
                result.data.cancelPipelineExecution,
                "Run cancelled."
              );
            }}
          />
          <MenuDivider />
          <MenuItem
            text="Delete"
            icon="trash"
            disabled={run.canCancel}
            onClick={async () => {
              const result = await destroy({ variables: { runId: run.runId } });
              showToastFor(result.data.deletePipelineRun, "Run deleted.");
            }}
          />
        </Menu>
      }
      position={"bottom"}
    >
      <Button minimal={true} icon="more" />
    </Popover>
  );
};

class RunTime extends React.Component<{
  startUnix: number | null;
  endUnix: number | null;
}> {
  _interval?: NodeJS.Timer;
  _timeout?: NodeJS.Timer;

  componentDidMount() {
    if (this.props.endUnix) return;

    // align to the next second and then update every second so the elapsed
    // time "ticks" up. Our render method uses Date.now(), so all we need to
    // do is force another React render. We could clone the time into React
    // state but that is a bit messier.
    setTimeout(() => {
      this.forceUpdate();
      this._interval = setInterval(() => this.forceUpdate(), 1000);
    }, Date.now() % 1000);
  }

  componentWillUnmount() {
    if (this._timeout) clearInterval(this._timeout);
    if (this._interval) clearInterval(this._interval);
  }

  render() {
    const start = this.props.startUnix ? this.props.startUnix * 1000 : 0;
    const end = this.props.endUnix ? this.props.endUnix * 1000 : Date.now();

    return (
      <div>
        <Icon icon="time" /> {start ? formatElapsedTime(end - start) : ""}
      </div>
    );
  }
}

function showToastFor(
  possibleError: { __typename: string; message?: string },
  successMessage: string
) {
  if ("message" in possibleError) {
    SharedToaster.show({
      message: possibleError.message,
      icon: "error",
      intent: Intent.DANGER
    });
  } else {
    SharedToaster.show({
      message: successMessage,
      icon: "confirm",
      intent: Intent.SUCCESS
    });
  }
}
