import * as React from "react";
import * as yaml from "yaml";
import gql from "graphql-tag";
import styled from "styled-components";
import { IconNames } from "@blueprintjs/icons";
import { Colors } from "@blueprintjs/core";
import { MutationFunction, Mutation } from "react-apollo";
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
import {
  RunPipelineRunEventFragment_ExecutionStepFailureEvent,
  RunPipelineRunEventFragment
} from "./types/RunPipelineRunEventFragment";

interface IRunProps {
  client: ApolloClient<any>;
  run?: RunFragment;
}

interface IRunState {
  logsFilter: ILogFilter;
  highlightedError?: { message: string; stack: string[] };
}

export class Run extends React.Component<IRunProps, IRunState> {
  static fragments = {
    RunFragment: gql`
      fragment RunFragment on PipelineRun {
        ...RunStatusPipelineRunFragment

        environmentConfigYaml
        runId
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
    stepKey?: string
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
      variables.reexecutionConfig = {
        previousRunId: run.runId,
        stepOutputHandles: []
      };

      step.inputs.forEach(input => {
        const deps = input.dependsOn;
        deps.forEach(dep => {
          dep.outputs.forEach(outputOfDependentStep => {
            variables.reexecutionConfig!.stepOutputHandles.push({
              stepKey: dep.key,
              outputName: outputOfDependentStep.name
            });
          });
        });
      });
    }

    const result = await mutation({ variables });

    handleStartExecutionResult(run.pipeline.name, result, {
      openInNewWindow: false
    });
  };

  render() {
    const { client, run } = this.props;
    const { logsFilter, highlightedError } = this.state;

    const stepKeysToExecute: (string | null)[] | null = run
      ? run.stepKeysToExecute
      : null;

    const executionPlan: RunFragment_executionPlan =
      run && run.executionPlan
        ? run.executionPlan
        : { __typename: "ExecutionPlan", steps: [], artifactsPersisted: false };

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
                          <ExecutionStartButton
                            title="Re-execute"
                            icon={IconNames.REPEAT}
                            small={true}
                            onClick={() => this.onReexecute(reexecuteMutation)}
                          />
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
  background: ${Colors.LIGHT_GRAY5};
`;
