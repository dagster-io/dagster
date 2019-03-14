import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors, NonIdealState, Classes, Dialog } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
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
import RunMetadataProvider from "./RunMetadataProvider";
import LogsToolbar from "./LogsToolbar";
import { PipelineRunExecutionPlanFragment_executionPlan } from "./types/PipelineRunExecutionPlanFragment";

interface IPipelineRunProps {
  plan: PipelineRunExecutionPlanFragment_executionPlan;
  run: PipelineRunFragment;
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
        ...PipelineRunExecutionPlanFragment
      }

      ${RunMetadataProvider.fragments.RunMetadataProviderMessageFragment}
      ${PipelineRunExecutionPlan.fragments.PipelineRunExecutionPlanFragment}
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
    highlightedError: undefined,
    logsVH: 40,
    logsFilter: DefaultLogFilter
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
    const { logsFilter, logsVH, highlightedError } = this.state;
    const { logs } = this.props.run;

    return (
      <PipelineRunWrapper>
        <RunMetadataProvider logs={logs.nodes}>
          {metadata => (
            <PipelineRunExecutionPlan
              run={this.props.run}
              runMetadata={metadata}
              onShowStateDetails={this.onShowStateDetails}
              onApplyStepFilter={stepName =>
                this.setState({
                  logsFilter: { ...logsFilter, text: `step:${stepName}` }
                })
              }
            />
          )}
        </RunMetadataProvider>
        <PanelDivider
          onMove={(vh: number) => this.setState({ logsVH: 100 - vh })}
          axis="vertical"
        />
        <LogsContainer style={{ height: `${logsVH}vh` }}>
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

export class PipelineRunEmpty extends React.Component {
  render() {
    return (
      <PipelineRunWrapper>
        <NonIdealState
          icon={IconNames.SEND_TO_GRAPH}
          title="No Run Data"
          description={
            "Provide configuration and click Play to execute the pipeline."
          }
        />
      </PipelineRunWrapper>
    );
  }
}

const PipelineRunWrapper = styled.div`
  display: flex;
  flex-direction: column;
  flex: 1 1;
  min-height: 0;
`;

const LogsContainer = styled.div`
  display: flex;
  flex-direction: column;
  background: ${Colors.LIGHT_GRAY5};
`;
