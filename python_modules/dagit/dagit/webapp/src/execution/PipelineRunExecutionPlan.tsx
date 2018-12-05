import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import {
  PipelineRunExecutionPlanFragment,
  PipelineRunExecutionPlanFragment_logs_nodes
} from "./types/PipelineRunExecutionPlanFragment";

interface IPipelineRunExecutionPlanProps {
  pipelineRun: PipelineRunExecutionPlanFragment;
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
            }
          }
        }
      }
    `
  };

  render() {
    return (
      <ExecutionPlanContainer>
        <ExecutionPlanContainerInner>
          <ExecutionTimeline />
          <ExecutionTimelineMessage>
            <ExecutionTimelineDot />{" "}
            {this.props.pipelineRun.logs.nodes.length > 0
              ? this.props.pipelineRun.logs.nodes[0].message
              : null}
          </ExecutionTimelineMessage>
          {this.props.pipelineRun.executionPlan.steps.map(step => {
            const metadata = stepMetadataFromLogs(
              step.name,
              this.props.pipelineRun.logs.nodes
            );
            return (
              <ExecutionPlanBox key={step.name} state={metadata.state}>
                <ExecutionStateDot state={metadata.state} />
                <ExecutionPlanBoxName>{step.name}</ExecutionPlanBoxName>
                {metadata.elapsed > 0 && (
                  <ExecutionStateLabel>
                    {Math.ceil(metadata.elapsed)} sec
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
  elapsed: number;
}

function stepMetadataFromLogs(
  name: string,
  logs: Array<PipelineRunExecutionPlanFragment_logs_nodes>
) {
  const START = new RegExp(`Beginning execution of ${name}`);
  const COMPLETION = new RegExp(`Execution of ${name} ([\\w]+) in ([\\d.]+)`);

  const metadata: IStepMetadata = {
    state: "waiting",
    elapsed: 0
  };

  logs.forEach(log => {
    if (START.exec(log.message)) {
      metadata.state = "running";
    }
    let match = COMPLETION.exec(log.message);
    if (match != null) {
      metadata.state = match[1] === "succeeded" ? "succeeded" : "failed";
      metadata.elapsed = Number.parseFloat(match[2]);
    }
  });

  return metadata;
}

const ExecutionPlanContainer = styled.div`
  flex: 2;
  overflow-y: scroll;
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
  top: 10px;
  left: 22px;
  bottom: 10px;
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
