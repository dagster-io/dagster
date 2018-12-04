import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { ExecutionTab, ExecutionTabs } from "./ExecutionTabs";
import PipelineRunLogs from "./PipelineRunLogs";
import { PipelineRunsLogsFragment } from "./types/PipelineRunsLogsFragment";
import { Colors } from "@blueprintjs/core";

interface IPipelineRunsLogsProps {
  runs: Array<PipelineRunsLogsFragment>;
  selectedRun: string | null;
  onSelectRun: (newRun: string) => void;
}

export default class PipelineRunsLogs extends React.Component<
  IPipelineRunsLogsProps
> {
  static fragments = {
    PipelineRunsLogsFragment: gql`
      fragment PipelineRunsLogsFragment on PipelineRun {
        runId
        status
        logs {
          pageInfo {
            lastCursor
          }
          nodes {
            ...PipelineRunLogsFragment
          }
        }
      }

      ${PipelineRunLogs.fragments.PipelineRunLogsFragment}
    `
  };

  renderTabs() {
    return this.props.runs.map((run, i) => {
      return (
        <ExecutionTab
          key={i}
          title={`Run ${i + 1}`}
          active={run.runId === this.props.selectedRun}
          onClick={() => this.props.onSelectRun(run.runId)}
        />
      );
    });
  }

  renderLogs() {
    const selectedRun = this.props.runs.find(
      ({ runId }) => runId === this.props.selectedRun
    );
    if (selectedRun) {
      return <PipelineRunLogs logs={selectedRun.logs.nodes} />;
    } else {
      return null;
    }
  }

  render() {
    return (
      <PipelineRunsLogsContainer>
        <ExecutionTabs>{this.renderTabs()}</ExecutionTabs>
        {this.renderLogs()}
      </PipelineRunsLogsContainer>
    );
  }
}

const PipelineRunsLogsContainer = styled.div`
  flex: 1 1;
  flex-direction: column;
  display: flex;
  background: ${Colors.BLACK};
`;
