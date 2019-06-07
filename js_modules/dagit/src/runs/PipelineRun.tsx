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
  PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent,
  PipelineRunFragment_executionPlan
} from "./types/PipelineRunFragment";
import { PanelDivider } from "../PanelDivider";
import PythonErrorInfo from "../PythonErrorInfo";
import { ExecutionPlan } from "../ExecutionPlan";
import RunMetadataProvider from "../RunMetadataProvider";
import LogsToolbar from "./LogsToolbar";
import { Mutation, MutationFn } from "react-apollo";
import {
  HANDLE_START_EXECUTION_FRAGMENT,
  handleStartExecutionResult
} from "./RunUtils";
import { ReexecuteStep, ReexecuteStepVariables } from "./types/ReexecuteStep";
import { ReexecutionConfig } from "src/types/globalTypes";
import RunSubscriptionProvider from "./RunSubscriptionProvider";
import { RunStatusToPageAttributes } from "./RunStatusToPageAttributes";
import ApolloClient from "apollo-client";

interface IPipelineRunProps {
  client: ApolloClient<any>;
  run?: PipelineRunFragment;
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
        ...RunStatusPipelineRunFragment
        ...RunSubscriptionPipelineRunFragment

        environmentConfigYaml
        runId
        mode
        pipeline {
          name
          solids {
            name
          }
        }
        logs {
          nodes {
            ...LogsFilterProviderMessageFragment
            ...LogsScrollingTableMessageFragment
            ...RunMetadataProviderMessageFragment
            ... on ExecutionStepFailureEvent {
              step {
                key
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

      ${ExecutionPlan.fragments.ExecutionPlanFragment}
      ${LogsFilterProvider.fragments.LogsFilterProviderMessageFragment}
      ${LogsScrollingTable.fragments.LogsScrollingTableMessageFragment}
      ${RunStatusToPageAttributes.fragments.RunStatusPipelineRunFragment}
      ${RunMetadataProvider.fragments.RunMetadataProviderMessageFragment}
      ${RunSubscriptionProvider.fragments.RunSubscriptionPipelineRunFragment}
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

  onShowStateDetails = (stepKey: string) => {
    const { run } = this.props;
    if (!run) return;

    const errorNode = run.logs.nodes.find(
      node =>
        node.__typename === "ExecutionStepFailureEvent" &&
        node.step != null &&
        node.step.key === stepKey
    ) as PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent;

    if (errorNode) {
      this.setState({ highlightedError: errorNode.error });
    }
  };

  onReexecuteStep = async (
    mutation: MutationFn<ReexecuteStep, ReexecuteStepVariables>,
    stepKey: string
  ) => {
    const { run } = this.props;
    if (!run) return;
    const step = run.executionPlan.steps.find(s => s.key === stepKey);
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
        executionParams: {
          selector: {
            name: run.pipeline.name,
            solidSubset: run.pipeline.solids.map(s => s.name)
          },
          environmentConfigData: yaml.parse(run.environmentConfigYaml),
          stepKeys: [stepKey],
          mode: run.mode
        },
        reexecutionConfig: reexecutionConfig
      }
    });

    handleStartExecutionResult(run.pipeline.name, result);
  };

  render() {
    const { client, run } = this.props;
    const { logsFilter, logsVW, highlightedError } = this.state;

    const logs = run ? run.logs.nodes : undefined;
    const executionPlan: PipelineRunFragment_executionPlan = run
      ? run.executionPlan
      : { __typename: "ExecutionPlan", steps: [], artifactsPersisted: false };

    return (
      <PipelineRunWrapper>
        {run && <RunSubscriptionProvider client={client} run={run} />}
        {run && <RunStatusToPageAttributes run={run} />}

        <LogsContainer style={{ width: `${logsVW}vw` }}>
          <LogsFilterProvider filter={logsFilter} nodes={logs}>
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
            <RunMetadataProvider logs={logs || []}>
              {metadata => (
                <ExecutionPlan
                  runMetadata={metadata}
                  executionPlan={executionPlan}
                  onShowStateDetails={this.onShowStateDetails}
                  onReexecuteStep={stepKey =>
                    this.onReexecuteStep(reexecuteMutation, stepKey)
                  }
                  onApplyStepFilter={stepKey =>
                    this.setState({
                      logsFilter: { ...logsFilter, text: `step:${stepKey}` }
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
    $executionParams: ExecutionParams!
    $reexecutionConfig: ReexecutionConfig
  ) {
    startPipelineExecution(
      executionParams: $executionParams
      reexecutionConfig: $reexecutionConfig
    ) {
      ...HandleStartExecutionFragment
    }
  }

  ${HANDLE_START_EXECUTION_FRAGMENT}
`;

export const PIPELINE_RUN_LOGS_UPDATE_FRAGMENT = gql`
  fragment PipelineRunLogsUpdateFragment on PipelineRun {
    runId
    status
    ...PipelineRunFragment
    logs {
      nodes {
        ...PipelineRunPipelineRunEventFragment
      }
    }
  }

  ${PipelineRun.fragments.PipelineRunFragment}
  ${PipelineRun.fragments.PipelineRunPipelineRunEventFragment}
`;

export const PIPELINE_RUN_LOGS_SUBSCRIPTION = gql`
  subscription PipelineRunLogsSubscription($runId: ID!, $after: Cursor) {
    pipelineRunLogs(runId: $runId, after: $after) {
      __typename
      ... on PipelineRunLogsSubscriptionSuccess {
        messages {
          ... on MessageEvent {
            runId
          }
          ...PipelineRunPipelineRunEventFragment
        }
      }
      ... on PipelineRunLogsSubscriptionMissingRunIdFailure {
        missingRunId
      }
    }
  }

  ${PipelineRun.fragments.PipelineRunPipelineRunEventFragment}
`;
