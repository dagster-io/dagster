import * as React from "react";
import * as yaml from "yaml";
import gql from "graphql-tag";
import styled from "styled-components";
import { IconNames } from "@blueprintjs/icons";
import { Colors, Button, Intent, Tooltip, Position } from "@blueprintjs/core";
import { MutationFunction, Mutation, useMutation } from "react-apollo";
import ApolloClient from "apollo-client";

import { ILogFilter, LogsProvider, GetDefaultLogFilter } from "./LogsProvider";
import LogsScrollingTable from "./LogsScrollingTable";
import { RunFragment, RunFragment_executionPlan } from "./types/RunFragment";
import { SplitPanelChildren } from "../SplitPanelChildren";
import { ExecutionPlan } from "../plan/ExecutionPlan";
import { RunMetadataProvider } from "../RunMetadataProvider";
import LogsToolbar from "./LogsToolbar";
import { handleStartExecutionResult, REEXECUTE_MUTATION } from "./RunUtils";
import { Reexecute, ReexecuteVariables } from "./types/Reexecute";
import { RunStatusToPageAttributes } from "./RunStatusToPageAttributes";
import ExecutionStartButton from "../execute/ExecutionStartButton";
import InfoModal from "../InfoModal";
import PythonErrorInfo from "../PythonErrorInfo";
import { RunContext } from "./RunContext";
import { PipelineRunStatus } from "../types/globalTypes";

import {
  RunPipelineRunEventFragment_ExecutionStepFailureEvent,
  RunPipelineRunEventFragment
} from "./types/RunPipelineRunEventFragment";
import { CANCEL_MUTATION } from "./RunUtils";
import { SharedToaster } from "../Util";

const REEXECUTE_DESCRIPTION = "Re-execute the pipeline run from scratch";
const REEXECUTE_PIPELINE_UNKNOWN =
  "Re-execute is unavailable because the pipeline is not present in the current repository.";
const RETRY_DESCRIPTION =
  "Retries the pipeline run, skipping steps that completed successfully";
const RETRY_DISABLED =
  "Retries are only enabled on persistent storage. Try rerunning with a different storage configuration.";
const RETRY_PIPELINE_UNKNOWN =
  "Retry is unavailable because the pipeline is not present in the current repository.";

interface IRunProps {
  client: ApolloClient<any>;
  run?: RunFragment;
}

interface IRunState {
  logsFilter: ILogFilter;
  highlightedError?: { message: string; stack: string[] };
}

const CancelRunButton: React.FunctionComponent<{ run: RunFragment }> = ({
  run
}) => {
  const [cancel] = useMutation(CANCEL_MUTATION);
  const [inFlight, setInFlight] = React.useState(false);
  return (
    <Button
      icon={IconNames.STOP}
      small={true}
      text="Terminate"
      intent="warning"
      disabled={inFlight}
      onClick={async () => {
        setInFlight(true);
        const res = await cancel({
          variables: { runId: run.runId }
        });
        setInFlight(false);
        if (
          res.data &&
          res.data.cancelPipelineExecution &&
          res.data.cancelPipelineExecution.message
        ) {
          SharedToaster.show({
            message: res.data.cancelPipelineExecution.message,
            icon: "error",
            intent: Intent.DANGER
          });
        }
      }}
    />
  );
};

export class Run extends React.Component<IRunProps, IRunState> {
  static fragments = {
    RunFragment: gql`
      fragment RunFragment on PipelineRun {
        ...RunStatusPipelineRunFragment

        environmentConfigYaml
        runId
        canCancel
        status
        mode
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
          artifactsPersisted
        }
        stepKeysToExecute
      }

      ${ExecutionPlan.fragments.ExecutionPlanFragment}
      ${RunStatusToPageAttributes.fragments.RunStatusPipelineRunFragment}
    `,
    RunPipelineRunEventFragment: gql`
      fragment RunPipelineRunEventFragment on PipelineRunEvent {
        ... on MessageEvent {
          message
          timestamp
          level
          step {
            key
          }
        }
        ... on ExecutionStepFailureEvent {
          error {
            message
            stack
          }
        }
        ...LogsScrollingTableMessageFragment
        ...RunMetadataProviderMessageFragment
      }

      ${RunMetadataProvider.fragments.RunMetadataProviderMessageFragment}
      ${LogsScrollingTable.fragments.LogsScrollingTableMessageFragment}
    `
  };

  state: IRunState = {
    logsFilter: GetDefaultLogFilter(),
    highlightedError: undefined
  };

  onShowStateDetails = (
    stepKey: string,
    logs: RunPipelineRunEventFragment[]
  ) => {
    const errorNode = logs.find(
      node =>
        node.__typename === "ExecutionStepFailureEvent" &&
        node.step != null &&
        node.step.key === stepKey
    ) as RunPipelineRunEventFragment_ExecutionStepFailureEvent;

    if (errorNode) {
      this.setState({ highlightedError: errorNode.error });
    }
  };

  onReexecute = async (
    mutation: MutationFunction<Reexecute, ReexecuteVariables>,
    stepKey?: string,
    resumeRetry?: boolean
  ) => {
    const { run } = this.props;
    if (!run || run.pipeline.__typename === "UnknownPipeline") return;

    const variables: ReexecuteVariables = {
      executionParams: {
        mode: run.mode,
        environmentConfigData: yaml.parse(run.environmentConfigYaml),
        selector: {
          name: run.pipeline.name,
          solidSubset: run.pipeline.solids.map(s => s.name)
        }
      }
    };

    if (stepKey && run.executionPlan) {
      const step = run.executionPlan.steps.find(s => s.key === stepKey);
      if (!step) return;
      variables.executionParams.stepKeys = [stepKey];
      variables.executionParams.retryRunId = run.runId;
    } else if (resumeRetry) {
      variables.executionParams.retryRunId = run.runId;
    }

    const result = await mutation({ variables });

    handleStartExecutionResult(run.pipeline.name, result, {
      openInNewWindow: false
    });
  };

  renderRetry(
    reexecuteMutation: MutationFunction<Reexecute, ReexecuteVariables>
  ) {
    const { run } = this.props;
    if (!run || !run.executionPlan) {
      return null;
    }

    const isUnknown = run.pipeline.__typename === "UnknownPipeline";

    if (run.status !== PipelineRunStatus.FAILURE) {
      return null;
    }

    if (!run.executionPlan.artifactsPersisted) {
      return (
        <Tooltip
          hoverOpenDelay={300}
          content={RETRY_DISABLED}
          position={Position.BOTTOM}
        >
          <ExecutionStartButton
            title="Resume / Retry"
            icon={IconNames.DISABLE}
            small={true}
            disabled
            onClick={() => null}
          />
        </Tooltip>
      );
    }

    return (
      <Tooltip
        hoverOpenDelay={300}
        content={isUnknown ? RETRY_PIPELINE_UNKNOWN : RETRY_DESCRIPTION}
        position={Position.BOTTOM}
      >
        <ExecutionStartButton
          title="Resume / Retry"
          icon={IconNames.REPEAT}
          small={true}
          disabled={isUnknown}
          onClick={() => this.onReexecute(reexecuteMutation, undefined, true)}
        />
      </Tooltip>
    );
  }

  render() {
    const { client, run } = this.props;
    const { logsFilter, highlightedError } = this.state;

    const stepKeysToExecute: (string | null)[] | null = run
      ? run.stepKeysToExecute
      : null;

    const isUnknown = run?.pipeline.__typename === "UnknownPipeline";
    const executionPlan: RunFragment_executionPlan = run?.executionPlan || {
      __typename: "ExecutionPlan",
      steps: [],
      artifactsPersisted: false
    };

    return (
      <Mutation<Reexecute, ReexecuteVariables> mutation={REEXECUTE_MUTATION}>
        {reexecuteMutation => (
          <RunWrapper>
            <RunContext.Provider value={run}>
              {run && <RunStatusToPageAttributes run={run} />}
              <LogsProvider
                client={client}
                runId={run ? run.runId : ""}
                filter={logsFilter}
              >
                {({ filteredNodes, allNodes }) => (
                  <SplitPanelChildren
                    identifier="run"
                    leftInitialPercent={75}
                    leftMinWidth={680}
                    left={
                      <LogsContainer>
                        <LogsToolbar
                          showSpinner={false}
                          filter={logsFilter}
                          onSetFilter={filter =>
                            this.setState({ logsFilter: filter })
                          }
                        >
                          <Tooltip
                            hoverOpenDelay={300}
                            position={Position.BOTTOM}
                            content={
                              isUnknown
                                ? REEXECUTE_PIPELINE_UNKNOWN
                                : REEXECUTE_DESCRIPTION
                            }
                          >
                            <ExecutionStartButton
                              title="Re-execute"
                              icon={IconNames.REPEAT}
                              small={true}
                              disabled={isUnknown}
                              onClick={() =>
                                this.onReexecute(reexecuteMutation)
                              }
                            />
                          </Tooltip>
                          {run && run.canCancel ? (
                            <>
                              <div style={{ minWidth: 6 }} />
                              <CancelRunButton run={run} />
                            </>
                          ) : null}
                          {this.renderRetry(reexecuteMutation)}
                        </LogsToolbar>
                        <LogsScrollingTable
                          nodes={filteredNodes}
                          filterKey={JSON.stringify(logsFilter)}
                        />
                      </LogsContainer>
                    }
                    right={
                      <>
                        <RunMetadataProvider logs={allNodes}>
                          {metadata => (
                            <ExecutionPlan
                              run={run}
                              runMetadata={metadata}
                              executionPlan={executionPlan}
                              stepKeysToExecute={stepKeysToExecute}
                              onShowStateDetails={stepKey => {
                                this.onShowStateDetails(stepKey, allNodes);
                              }}
                              onReexecuteStep={stepKey =>
                                this.onReexecute(reexecuteMutation, stepKey)
                              }
                              onApplyStepFilter={stepKey =>
                                this.setState({
                                  logsFilter: {
                                    ...this.state.logsFilter,
                                    text: `step:${stepKey}`
                                  }
                                })
                              }
                            />
                          )}
                        </RunMetadataProvider>
                        {highlightedError && (
                          <InfoModal
                            onRequestClose={() =>
                              this.setState({ highlightedError: undefined })
                            }
                          >
                            <PythonErrorInfo error={highlightedError} />
                          </InfoModal>
                        )}
                      </>
                    }
                  />
                )}
              </LogsProvider>
            </RunContext.Provider>
          </RunWrapper>
        )}
      </Mutation>
    );
  }
}

const RunWrapper = styled.div`
  display: flex;
  flex-direction: row;
  flex: 1 1;
  min-height: 0;
`;

const LogsContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
  background: ${Colors.LIGHT_GRAY5};
`;
