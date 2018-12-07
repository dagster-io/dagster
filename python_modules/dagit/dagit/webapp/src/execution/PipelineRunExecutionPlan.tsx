import * as React from "react";
import gql from "graphql-tag";
import produce from "immer";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import {
  PipelineRunExecutionPlanFragment,
  PipelineRunExecutionPlanFragment_logs_nodes
} from "./types/PipelineRunExecutionPlanFragment";

interface IPipelineRunExecutionPlanProps {
  pipelineRun: PipelineRunExecutionPlanFragment;
  onSetLogFilter: (filter: string) => void;
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
      onSetLogFilter,
      pipelineRun: { logs, executionPlan }
    } = this.props;
    const stepMetadata = logsToStepMetadata(logs.nodes);

    return (
      <ExecutionPlanContainer>
        <ExecutionPlanContainerInner>
          <ExecutionTimeline />
          <ExecutionTimelineMessage>
            <ExecutionTimelineDot /> Execution started
          </ExecutionTimelineMessage>
          {executionPlan.steps.map(step => {
            const metadata = stepMetadata[step.name] || {
              state: "waiting"
            };
            return (
              <ExecutionPlanBox
                key={step.name}
                state={metadata.state}
                onClick={() => onSetLogFilter(step.name)}
              >
                <ExecutionStateDot state={metadata.state} />
                <ExecutionPlanBoxName>{step.name}</ExecutionPlanBoxName>
                {metadata.elapsed && (
                  <ExecutionStateLabel>
                    {Math.ceil(metadata.elapsed / 1000)} sec
                  </ExecutionStateLabel>
                )}
              </ExecutionPlanBox>
            );
          })}
        </ExecutionPlanContainerInner>
      </ExecutionPlanContainer>
    );
  }
}

type IStepMetadataState = "waiting" | "running" | "succeeded" | "failed";

interface IStepMetadata {
  state: IStepMetadataState;
  start?: number;
  elapsed?: number;
}

function logsToStepMetadata(
  logs: Array<PipelineRunExecutionPlanFragment_logs_nodes>
): { [stepName: string]: IStepMetadata } {
  const steps = {};
  logs.forEach(log => {
    if (log.__typename === "ExecutionStepStartEvent") {
      steps[log.step.name] = {
        state: "running",
        start: Number.parseInt(log.timestamp, 10)
      };
    } else if (log.__typename === "ExecutionStepSuccessEvent") {
      steps[log.step.name] = produce(steps[log.step.name] || {}, step => {
        step.state = "succeeded";
        if (step.start) {
          step.elapsed = Number.parseInt(log.timestamp, 10) - step.start;
        }
      });
    } else if (log.__typename === "ExecutionStepFailureEvent") {
      steps[log.step.name] = produce(steps[log.step.name] || {}, step => {
        step.state = "failed";
        if (step.start) {
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

const ExecutionPlanBoxName = styled.div`
  font-weight: 500;
`;

const ExecutionPlanBox = styled.div<{ state: IStepMetadataState }>`
  background: ${({ state }) =>
    state === "waiting" ? Colors.GRAY3 : Colors.LIGHT_GRAY2}
  box-shadow: 0 2px 3px rgba(0, 0, 0, 0.3);
  color: ${Colors.DARK_GRAY3};
  padding: 4px;
  padding-right: 10px;
  margin: 6px;
  margin-left: 15px;
  margin-bottom: 0;
  display: inline-flex;
  min-width: 150px;
  align-items: center;
  border-radius: 3px;
  position: relative;
  z-index: 2;
  &:hover {
    cursor: default;
    background: ${({ state }) =>
      state === "waiting" ? Colors.LIGHT_GRAY4 : Colors.WHITE}
  }
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
  width: 9px;
  height: 9px;
  border-radius: 4px;
  margin-right: 8px;
  background: #232b2f;
  border: 1px solid ${Colors.LIGHT_GRAY2};
  margin-left: 18px;
  flex-shrink: 0;
`;

const ExecutionStateDot = styled.div<{ state: IStepMetadataState }>`
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 4px;
  margin-right: 9px;
  background: ${({ state }) =>
    ({
      waiting: Colors.GRAY1,
      running: Colors.GRAY3,
      succeeded: Colors.GREEN2,
      failed: Colors.RED3
    }[state])};
`;

const ExecutionStateLabel = styled.div`
  opacity: 0.7;
  font-size: 0.9em;
  margin-left: 10px;
`;
