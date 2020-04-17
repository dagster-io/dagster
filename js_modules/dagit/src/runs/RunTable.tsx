import * as React from "react";
import * as qs from "query-string";
import gql from "graphql-tag";
import {
  Button,
  Icon,
  Menu,
  MenuItem,
  Popover,
  MenuDivider,
  NonIdealState,
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
  handleReexecutionResult,
  START_PIPELINE_REEXECUTION_MUTATION,
  DELETE_MUTATION,
  CANCEL_MUTATION,
  getReexecutionVariables
} from "./RunUtils";
import { RunTag } from "./RunTag";
import { formatElapsedTime, unixTimestampToString } from "../Util";
import { SharedToaster } from "../DomUtils";

import { HighlightedCodeBlock } from "../HighlightedCodeBlock";
import { Link } from "react-router-dom";
import {
  RunTableRunFragment,
  RunTableRunFragment_tags
} from "./types/RunTableRunFragment";
import { showCustomAlert } from "../CustomAlertProvider";
import { useMutation, useLazyQuery } from "react-apollo";
import { RUNS_ROOT_QUERY, RunsQueryVariablesContext } from "./RunsRoot";
import PythonErrorInfo from "../PythonErrorInfo";
import { TokenizingFieldValue } from "../TokenizingField";

interface RunTableProps {
  runs: RunTableRunFragment[];
  onSetFilter: (search: TokenizingFieldValue[]) => void;
}

// Avoid fetching envYaml on load in Runs page. It is slow.
const PipelineEnvironmentYamlQuery = gql`
  query PipelineEnvironmentYamlQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      ... on PipelineRun {
        environmentConfigYaml
      }
    }
  }
`;

export class RunTable extends React.Component<RunTableProps> {
  static fragments = {
    RunTableRunFragment: gql`
      fragment RunTableRunFragment on PipelineRun {
        runId
        status
        stepKeysToExecute
        canCancel
        mode
        rootRunId
        parentRunId
        pipelineSnapshotId
        pipeline {
          __typename

          ... on PipelineReference {
            name
          }
          ... on Pipeline {
            pipelineSnapshotId
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
          ...PythonErrorFragment
        }
        tags {
          key
          value
        }
      }

      ${PythonErrorInfo.fragments.PythonErrorFragment}
    `
  };

  render() {
    if (this.props.runs.length === 0) {
      return (
        <div style={{ marginTop: 100 }}>
          <NonIdealState
            icon="history"
            title="Pipeline Runs"
            description="No runs to display. Use the Playground to start a pipeline."
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
          <RunRow
            run={run}
            key={run.runId}
            onSetFilter={this.props.onSetFilter}
          />
        ))}
      </div>
    );
  }
}

const RunRow: React.FunctionComponent<{
  run: RunTableRunFragment;
  onSetFilter: (search: TokenizingFieldValue[]) => void;
}> = ({ run, onSetFilter }) => {
  let details;
  let time;
  if (run.stats.__typename === "PipelineRunStatsSnapshot") {
    details = (
      <Details>
        <Link
          to={`/runs/${run.pipeline.name}/${run.runId}?q=type:step_success`}
        >{`${run.stats.stepsSucceeded} steps succeeded, `}</Link>
        <Link
          to={`/runs/${run.pipeline.name}/${run.runId}?q=type:step_failure`}
        >
          {`${run.stats.stepsFailed} steps failed, `}{" "}
        </Link>
        <Link
          to={`/runs/${run.pipeline.name}/${run.runId}?q=type:materialization`}
        >{`${run.stats.materializations} materializations`}</Link>
        ,{" "}
        <Link
          to={`/runs/${run.pipeline.name}/${run.runId}?q=type:expectation`}
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

  const onTagClick = (tag: RunTableRunFragment_tags) => {
    onSetFilter([{ token: "tag", value: `${tag.key}=${tag.value}` }]);
  };

  let pipelineLink = `/pipeline/${run.pipeline.name}@${run.pipelineSnapshotId}/`;
  if (
    run.pipeline.__typename === "Pipeline" &&
    run.pipeline.pipelineSnapshotId === run.pipelineSnapshotId
  ) {
    // If the pipeline snapshot is still current, go to the live view not the snapshot.
    pipelineLink = `/pipeline/${run.pipeline.name}/`;
  }

  return (
    <RowContainer key={run.runId} style={{ paddingRight: 3 }}>
      <RowColumn style={{ maxWidth: 30, paddingLeft: 0, textAlign: "center" }}>
        <RunStatus status={run.status} />
      </RowColumn>
      <RowColumn style={{ flex: 2.4 }}>
        <Link to={`/runs/${run.pipeline.name}/${run.runId}`}>
          {titleForRun(run)}
        </Link>
        {details}
      </RowColumn>
      <RowColumn>
        <Link to={pipelineLink}>
          <Icon icon="diagram-tree" /> {run.pipeline.name}
        </Link>
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
          <RunTags tags={run.tags} onClick={onTagClick} />
        </div>
      </RowColumn>
      <RowColumn style={{ flex: 1.8, borderRight: 0 }}>{time}</RowColumn>
      <RowColumn style={{ maxWidth: 50 }}>
        <RunActionsMenu run={run} />
      </RowColumn>
    </RowContainer>
  );
};

const RunTags: React.FunctionComponent<{
  tags: RunTableRunFragment_tags[];
  onClick?: (tag: { key: string; value: string }) => void;
}> = ({ tags, onClick }) => {
  const [open, setOpen] = React.useState(false);

  if (!tags.length) {
    return null;
  }

  return (
    <div
      style={{
        display: "flex",
        width: "100%",
        height: open ? undefined : 22,
        position: "relative",
        overflow: "hidden"
      }}
    >
      <div
        style={{
          position: "relative",
          minWidth: open ? undefined : "fit-content",
          width: "100%",
          whiteSpace: open ? "pre-wrap" : "nowrap",
          display: open ? "block" : "flex",
          flexDirection: open ? undefined : "row"
        }}
      >
        {tags.map((tag, idx) => (
          <RunTag tag={tag} key={idx} onClick={onClick} />
        ))}
        <div
          style={{
            display: open ? "none" : "block",
            margin: 0,
            position: "absolute",
            height: 22,
            zIndex: 2,
            right: 0,
            bottom: 0,
            padding: "0 5px",
            backgroundColor: "#ffffff",
            userSelect: "none",
            color: "#ffffff"
          }}
        >
          ...
        </div>
      </div>
      <div
        style={{
          display: open ? "none" : "block",
          margin: 0,
          position: "absolute",
          height: 24,
          zIndex: 1,
          right: 0,
          bottom: 0,
          padding: "0 10px",
          textAlign: "center",
          backgroundColor: "#ffffff",
          cursor: "pointer"
        }}
        onClick={() => setOpen(true)}
      >
        ...
      </div>
    </div>
  );
};

const RunActionsMenu: React.FunctionComponent<{
  run: RunTableRunFragment;
}> = ({ run }) => {
  const variables = React.useContext(RunsQueryVariablesContext);
  const [reexecute] = useMutation(START_PIPELINE_REEXECUTION_MUTATION);
  const [cancel] = useMutation(CANCEL_MUTATION, {
    refetchQueries: [{ query: RUNS_ROOT_QUERY, variables }]
  });
  const [destroy] = useMutation(DELETE_MUTATION, {
    refetchQueries: [{ query: RUNS_ROOT_QUERY, variables }]
  });
  const [loadEnv, { called, loading, data }] = useLazyQuery(
    PipelineEnvironmentYamlQuery,
    {
      variables: { runId: run.runId }
    }
  );

  const envYaml = data?.pipelineRunOrError?.environmentConfigYaml;
  const infoReady = run.pipeline.__typename === "Pipeline" && envYaml != null;
  return (
    <Popover
      content={
        <Menu>
          <MenuItem
            text={
              loading ? "Loading Configuration..." : "View Configuration..."
            }
            disabled={envYaml == null}
            icon="share"
            onClick={() =>
              showCustomAlert({
                title: "Config",
                body: (
                  <HighlightedCodeBlock value={envYaml} languages={["yaml"]} />
                )
              })
            }
          />
          <MenuDivider />

          <MenuItem
            text="Open in Playground..."
            disabled={!infoReady}
            icon="edit"
            target="_blank"
            href={`/playground/${run.pipeline.name}/setup?${qs.stringify({
              mode: run.mode,
              config: envYaml,
              solidSubset:
                run.pipeline.__typename === "Pipeline"
                  ? run.pipeline.solids.map(s => s.name)
                  : []
            })}`}
          />
          <MenuItem
            text="Re-execute"
            disabled={!infoReady}
            icon="repeat"
            onClick={async () => {
              const result = await reexecute({
                variables: getReexecutionVariables({
                  run,
                  envYaml
                })
              });
              handleReexecutionResult(run.pipeline.name, result, {
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
      onOpening={() => {
        if (!called) {
          loadEnv();
        }
      }}
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
