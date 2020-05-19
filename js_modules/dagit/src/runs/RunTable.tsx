import * as React from "react";
import gql from "graphql-tag";
import {
  Legend,
  LegendColumn,
  RowColumn,
  RowContainer
} from "../ListComponents";
import { RunTag } from "./RunTag";
import {
  RunTableRunFragment,
  RunTableRunFragment_tags
} from "./types/RunTableRunFragment";
import { TokenizingFieldValue } from "../TokenizingField";
import { RUNS_ROOT_QUERY, RunsQueryVariablesContext } from "./RunsRoot";
import PythonErrorInfo from "../PythonErrorInfo";
import { NonIdealState, Icon } from "@blueprintjs/core";
import { Link } from "react-router-dom";
import {
  RunStatus,
  titleForRun,
  RunActionsMenu,
  RunTime,
  RunStatsDetails,
  RunComponentFragments
} from "./RunUtils";

interface RunTableProps {
  runs: RunTableRunFragment[];
  onSetFilter: (search: TokenizingFieldValue[]) => void;
}

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
        tags {
          key
          value
        }
        ...RunStatsDetailFragment
        ...RunTimeFragment
      }

      ${PythonErrorInfo.fragments.PythonErrorFragment}
      ${RunComponentFragments.STATS_DETAIL_FRAGMENT}
      ${RunComponentFragments.RUN_TIME_FRAGMENT}
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
  const variables = React.useContext(RunsQueryVariablesContext);

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

  const refetchQueries = [{ query: RUNS_ROOT_QUERY, variables }];

  return (
    <RowContainer key={run.runId} style={{ paddingRight: 3 }}>
      <RowColumn style={{ maxWidth: 30, paddingLeft: 0, textAlign: "center" }}>
        <RunStatus status={run.status} />
      </RowColumn>
      <RowColumn style={{ flex: 2.4 }}>
        <Link to={`/runs/${run.pipeline.name}/${run.runId}`}>
          {titleForRun(run)}
        </Link>
        <RunStatsDetails run={run} />
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
      <RowColumn style={{ flex: 1.8, borderRight: 0 }}>
        <RunTime run={run} />
      </RowColumn>
      <RowColumn style={{ maxWidth: 50 }}>
        <RunActionsMenu run={run} refetchQueries={refetchQueries} />
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
