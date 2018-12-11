import * as React from "react";
import gql from "graphql-tag";
import produce from "immer";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import {
  PipelineRunExecutionPlanFragment,
  PipelineRunExecutionPlanFragment_logs_nodes
} from "./types/PipelineRunExecutionPlanFragment";
import { ExecutionPlanBox } from "./PipelineRunExecutionPlanBox";

interface IPipelineRunExecutionPlanProps {
  pipelineRun: PipelineRunExecutionPlanFragment;
  onApplyStepFilter: (step: string) => void;
  onShowStateDetails: (step: string) => void;
}

export default class PipelineRunExecutionPlan extends React.Component<
  IPipelineRunExecutionPlanProps
> {
  static fragments = {
    PipelineRunExecutionPlanFragment: gql`
      fragment PipelineRunExecutionPlanFragment on PipelineRun {
        executionPlan {
          steps {
            name
            solid {
              name
            }
            tag
          }
        }
        logs {
          nodes {
            __typename
            ... on MessageEvent {
              message
              timestamp
            }

            ... on ExecutionStepEvent {
              step {
                name
              }
            }
          }
        }
      }
    `,
    PipelineRunExecutionPlanPipelineRunEventFragment: gql`
      fragment PipelineRunExecutionPlanPipelineRunEventFragment on PipelineRunEvent {
        __typename
        ... on MessageEvent {
          message
          timestamp
        }

        ... on ExecutionStepEvent {
          step {
            name
          }
        }
      }
    `
  };

  render() {
    const {
      onApplyStepFilter,
      onShowStateDetails,
      pipelineRun: { logs, executionPlan }
    } = this.props;
    const stepMetadata = logsToStepMetadata(logs.nodes);
    const stepsOrderedByTransitionTime = Object.keys(stepMetadata).sort(
      (a, b) => stepMetadata[b].transitionedAt - stepMetadata[a].transitionedAt
    );

    return (
      <ExecutionPlanContainer>
        <ExecutionPlanContainerInner>
          <ExecutionTimeline />
          <ExecutionTimelineMessage>
            <ExecutionTimelineDot /> Execution started
          </ExecutionTimelineMessage>
          {executionPlan.steps.map(step => {
            const delay = stepsOrderedByTransitionTime.indexOf(step.name) * 100;
            const metadata = stepMetadata[step.name] || {
              state: IStepState.WAITING
            };
            return (
              <ExecutionPlanBox
                key={step.name}
                state={metadata.state}
                elapsed={metadata.elapsed}
                name={step.name}
                onShowStateDetails={onShowStateDetails}
                onApplyStepFilter={onApplyStepFilter}
                delay={delay}
              />
            );
          })}
        </ExecutionPlanContainerInner>
      </ExecutionPlanContainer>
    );
  }
}

export enum IStepState {
  WAITING = "waiting",
  RUNNING = "running",
  SUCCEEDED = "succeeded",
  FAILED = "failed"
}

export interface IStepMetadata {
  state: IStepState;
  start?: number;
  elapsed?: number;
  transitionedAt: number;
}

function logsToStepMetadata(
  logs: Array<PipelineRunExecutionPlanFragment_logs_nodes>
): { [stepName: string]: IStepMetadata } {
  const steps = {};
  logs.forEach(log => {
    if (log.__typename === "ExecutionStepStartEvent") {
      steps[log.step.name] = {
        state: IStepState.RUNNING,
        start: Number.parseInt(log.timestamp, 10),
        transitionedAt: log.timestamp
      };
    } else if (log.__typename === "ExecutionStepSuccessEvent") {
      steps[log.step.name] = produce(steps[log.step.name] || {}, step => {
        step.state = IStepState.SUCCEEDED;
        if (step.start) {
          step.transitionedAt = log.timestamp;
          step.elapsed = Number.parseInt(log.timestamp, 10) - step.start;
        }
      });
    } else if (log.__typename === "ExecutionStepFailureEvent") {
      steps[log.step.name] = produce(steps[log.step.name] || {}, step => {
        step.state = IStepState.FAILED;
        if (step.start) {
          step.transitionedAt = log.timestamp;
          step.elapsed = Number.parseInt(log.timestamp, 10) - step.start;
        }
      });
    }
  });
  return steps;
}

const ExecutionPlanContainer = styled.div`
  flex: 1;
  overflow-y: scroll;
  color: ${Colors.WHITE};
  background: #232b2f;
`;

const ExecutionPlanContainerInner = styled.div`
  margin-top: 15px;
  position: relative;
  margin-bottom: 15px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  font-size: 0.9em;
`;

const ExecutionTimelineMessage = styled.div`
  display: flex;
  align-items: center;
  position: relative;
  color: ${Colors.LIGHT_GRAY2};
  z-index: 2;
`;

const ExecutionTimeline = styled.div`
  border-left: 1px solid ${Colors.GRAY3};
  position: absolute;
  top: 12px;
  left: 23px;
  bottom: 12px;
`;

const ExecutionTimelineDot = styled.div`
  display: inline-block;
  width: 11px;
  height: 11px;
  border-radius: 5.5px;
  margin-right: 8px;
  background: #232b2f;
  border: 1px solid ${Colors.LIGHT_GRAY2};
  margin-left: 18px;
  flex-shrink: 0;
`;
