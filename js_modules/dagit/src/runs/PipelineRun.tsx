import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors, Classes, Dialog } from "@blueprintjs/core";
import LogsFilterProvider, {
  ILogFilter,
  DefaultLogFilter
} from "./LogsFilterProvider";
import LogsScrollingTable from "./LogsScrollingTable";
import {
  PipelineRunFragment,
  PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent
} from "./types/PipelineRunFragment";
import { PanelDivider } from "../PanelDivider";
import PythonErrorInfo from "../PythonErrorInfo";
import ExecutionPlan from "../ExecutionPlan";
import RunMetadataProvider from "../RunMetadataProvider";
import LogsToolbar from "./LogsToolbar";

interface IPipelineRunProps {
  run: PipelineRunFragment;
}

interface IPipelineRunState {
  logsVW: number;
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
            ...RunMetadataProviderMessageFragment
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
        executionPlan {
          ...ExecutionPlanFragment
        }
      }

      ${RunMetadataProvider.fragments.RunMetadataProviderMessageFragment}
      ${ExecutionPlan.fragments.ExecutionPlanFragment}
      ${LogsFilterProvider.fragments.LogsFilterProviderMessageFragment}
      ${LogsScrollingTable.fragments.LogsScrollingTableMessageFragment}
    `,
    PipelineRunPipelineRunEventFragment: gql`
      fragment PipelineRunPipelineRunEventFragment on PipelineRunEvent {
        ...LogsScrollingTableMessageFragment
        ...LogsFilterProviderMessageFragment
        ...RunMetadataProviderMessageFragment
      }

      ${RunMetadataProvider.fragments.RunMetadataProviderMessageFragment}
      ${LogsFilterProvider.fragments.LogsFilterProviderMessageFragment}
      ${LogsScrollingTable.fragments.LogsScrollingTableMessageFragment}
    `
  };

  state = {
    logsVW: 75,
    logsFilter: DefaultLogFilter,
    highlightedError: undefined
  };

  onShowStateDetails = (step: string) => {
    const errorNode = this.props.run.logs.nodes.find(
      node =>
        node.__typename === "ExecutionStepFailureEvent" &&
        node.step != null &&
        node.step.name === step
    ) as PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent;

    if (errorNode) {
      this.setState({ highlightedError: errorNode.error });
    }
  };

  render() {
    const { logsFilter, logsVW, highlightedError } = this.state;
    const { logs } = this.props.run;

    return (
      <PipelineRunWrapper>
        <LogsContainer style={{ width: `${logsVW}vw` }}>
          <LogsFilterProvider filter={logsFilter} nodes={logs.nodes}>
            {({ filteredNodes, busy }) => (
              <>
                <LogsToolbar
                  showSpinner={busy}
                  filter={logsFilter}
                  onSetFilter={filter => this.setState({ logsFilter: filter })}
                />
                <LogsScrollingTable nodes={filteredNodes} />
              </>
            )}
          </LogsFilterProvider>
        </LogsContainer>
        <PanelDivider
          onMove={(vw: number) => this.setState({ logsVW: vw })}
          axis="horizontal"
        />
        <RunMetadataProvider logs={logs.nodes}>
          {metadata => (
            <ExecutionPlan
              runMetadata={metadata}
              executionPlan={this.props.run.executionPlan}
              onShowStateDetails={this.onShowStateDetails}
              onApplyStepFilter={stepName =>
                this.setState({
                  logsFilter: { ...logsFilter, text: `step:${stepName}` }
                })
              }
            />
          )}
        </RunMetadataProvider>
        <Dialog
          icon="info-sign"
          onClose={() => this.setState({ highlightedError: undefined })}
          style={{ width: "80vw", maxWidth: 1400 }}
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
const PipelineRunWrapper = styled.div`
  display: flex;
  flex-direction: row;
  flex: 1 1;
  min-height: 0;
`;

const LogsContainer = styled.div`
  display: flex;
  flex-direction: column;
  background: ${Colors.LIGHT_GRAY5};
`;
