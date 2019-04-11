import * as React from "react";
import * as yaml from "yaml";
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
import { Mutation, MutationFn } from "react-apollo";
import {
  HANDLE_START_EXECUTION_FRAGMENT,
  handleStartExecutionResult
} from "./RunUtils";
import { ReexecuteStep, ReexecuteStepVariables } from "./types/ReexecuteStep";
import { ReexecutionConfig } from "src/types/globalTypes";

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
        config
        runId
        pipeline {
          name
        }
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
          steps {
            key
            inputs {
              dependsOn {
                key
                outputs {
                  name
                  type {
                    name
                  }
                }
              }
            }
          }
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

  onReexecuteStep = async (
    mutation: MutationFn<ReexecuteStep, ReexecuteStepVariables>,
    stepName: string
  ) => {
    const { run } = this.props;

    const step = run.executionPlan.steps.find(s => s.key === stepName);
    if (!step) return;

    const reexecutionConfig: ReexecutionConfig = {
      previousRunId: run.runId,
      stepOutputHandles: []
    };

    step.inputs.forEach(input => {
      input.dependsOn.outputs.forEach(outputOfDependentStep => {
        reexecutionConfig.stepOutputHandles.push({
          stepKey: input.dependsOn.key,
          outputName: outputOfDependentStep.name
        });
      });
    });

    const result = await mutation({
      variables: {
        pipeline: { name: run.pipeline.name },
        config: yaml.parse(run.config),
        stepKeys: [stepName],
        reexecutionConfig: reexecutionConfig
      }
    });

    handleStartExecutionResult(run.pipeline.name, result);
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

        <Mutation<ReexecuteStep, ReexecuteStepVariables>
          mutation={REEXECUTE_STEP_MUTATION}
        >
          {reexecuteMutation => (
            <RunMetadataProvider logs={logs.nodes}>
              {metadata => (
                <ExecutionPlan
                  runMetadata={metadata}
                  executionPlan={this.props.run.executionPlan}
                  onShowStateDetails={this.onShowStateDetails}
                  onReexecuteStep={stepName =>
                    this.onReexecuteStep(reexecuteMutation, stepName)
                  }
                  onApplyStepFilter={stepName =>
                    this.setState({
                      logsFilter: { ...logsFilter, text: `step:${stepName}` }
                    })
                  }
                />
              )}
            </RunMetadataProvider>
          )}
        </Mutation>
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

const REEXECUTE_STEP_MUTATION = gql`
  mutation ReexecuteStep(
    $pipeline: ExecutionSelector!
    $config: PipelineConfig!
    $stepKeys: [String!]
    $reexecutionConfig: ReexecutionConfig
  ) {
    startPipelineExecution(
      pipeline: $pipeline
      config: $config
      stepKeys: $stepKeys
      reexecutionConfig: $reexecutionConfig
    ) {
      ...HandleStartExecutionFragment
    }
  }

  ${HANDLE_START_EXECUTION_FRAGMENT}
`;
