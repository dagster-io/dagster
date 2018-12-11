import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors, Button, Classes, Dialog } from "@blueprintjs/core";
import LogsFilterProvider, {
  ILogFilter,
  DefaultLogFilter
} from "./LogsFilterProvider";
import LogsScrollingTable from "./LogsScrollingTable";
import PipelineRunExecutionPlan from "./PipelineRunExecutionPlan";
import {
  PipelineRunFragment,
  PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent
} from "./types/PipelineRunFragment";
import { PanelDivider } from "../PanelDivider";
import PythonErrorInfo from "../PythonErrorInfo";
import LogsToolbar from "./LogsToolbar";

interface IPipelineRunProps {
  pipelineRun: PipelineRunFragment;
}

interface IPipelineRunState {
  logsVH: number;
  logsFilter: ILogFilter;
  highlightedError?: { message: string; stack: string[] };
}

export class PipelineRun extends React.Component<
  IPipelineRunProps,
  IPipelineRunState
> {
  static fragments = {
    PipelineRunFragment: gql`
      fragment PipelineRunFragment on PipelineRun {
        logs {
          nodes {
            ...LogsFilterProviderMessageFragment
            ...LogsScrollingTableMessageFragment
            ... on ExecutionStepFailureEvent {
              step {
                name
              }
              error {
                stack
                message
              }
            }
          }
        }
        ...PipelineRunExecutionPlanFragment
      }

      ${PipelineRunExecutionPlan.fragments.PipelineRunExecutionPlanFragment}
      ${LogsFilterProvider.fragments.LogsFilterProviderMessageFragment}
      ${LogsScrollingTable.fragments.LogsScrollingTableMessageFragment}
    `,
    PipelineRunPipelineRunEventFragment: gql`
      fragment PipelineRunPipelineRunEventFragment on PipelineRunEvent {
        ...LogsScrollingTableMessageFragment
        ...LogsFilterProviderMessageFragment
        ...PipelineRunExecutionPlanPipelineRunEventFragment
      }

      ${PipelineRunExecutionPlan.fragments
        .PipelineRunExecutionPlanPipelineRunEventFragment}
      ${LogsFilterProvider.fragments.LogsFilterProviderMessageFragment}
      ${LogsScrollingTable.fragments.LogsScrollingTableMessageFragment}
    `
  };

  state = {
    highlightedError: undefined,
    logsVH: 40,
    logsFilter: DefaultLogFilter
  };

  onShowStateDetails = (step: string) => {
    const errorNode = this.props.pipelineRun.logs.nodes.find(
      node =>
        node.__typename === "ExecutionStepFailureEvent" &&
        node.step.name === step
    ) as PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent;

    if (errorNode) {
      this.setState({ highlightedError: errorNode.error });
    }
  };

  render() {
    const { logsFilter, logsVH, highlightedError } = this.state;

    return (
      <PipelineRunWrapper>
        <PipelineRunExecutionPlan
          pipelineRun={this.props.pipelineRun}
          onShowStateDetails={this.onShowStateDetails}
          onApplyStepFilter={stepName =>
            this.setState({ logsFilter: { ...logsFilter, text: stepName } })
          }
        />
        <PanelDivider
          onMove={(vh: number) => this.setState({ logsVH: 100 - vh })}
          axis="vertical"
        />
        <LogsContainer style={{ height: `${logsVH}vh` }}>
          <LogsToolbar
            filter={logsFilter}
            onSetFilter={filter => this.setState({ logsFilter: filter })}
          />
          <LogsFilterProvider
            filter={logsFilter}
            nodes={this.props.pipelineRun.logs.nodes}
          >
            {nodes => <LogsScrollingTable nodes={nodes} />}
          </LogsFilterProvider>
        </LogsContainer>
        <Dialog
          icon="info-sign"
          onClose={() => this.setState({ highlightedError: undefined })}
          style={{ width: "80vw", maxWidth: 900, height: 415 }}
          title={"Error"}
          usePortal={true}
          isOpen={!!highlightedError}
        >
          <div className={Classes.DIALOG_BODY}>
            {highlightedError && <PythonErrorInfo error={highlightedError} />}
          </div>
        </Dialog>
      </PipelineRunWrapper>
    );
  }
}

export class PipelineRunEmpty extends React.Component {
  render() {
    return (
      <PipelineRunWrapper>
        Provide configuration and click the Play icon to execute the pipeline.
      </PipelineRunWrapper>
    );
  }
}

const PipelineRunWrapper = styled.div`
  display: flex;
  flex-direction: column;
  flex: 1 1;
`;

const LogsContainer = styled.div`
  display: flex;
  flex-direction: column;
  background: ${Colors.LIGHT_GRAY5};
`;
