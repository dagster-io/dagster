import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { PipelineRunExecutionPlanFragment } from "./types/PipelineRunExecutionPlanFragment";
import { ExecutionPlanBox } from "./PipelineRunExecutionPlanBox";
import { IStepMetadataDict, IStepState } from "./StepMetadataProvider";

interface IPipelineRunExecutionPlanProps {
  pipelineRun: PipelineRunExecutionPlanFragment;
  stepMetadata: IStepMetadataDict;
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
      }
    `
  };

  render() {
    const {
      onApplyStepFilter,
      onShowStateDetails,
      stepMetadata,
      pipelineRun: { executionPlan }
    } = this.props;

    const stepsOrderedByTransitionTime = Object.keys(stepMetadata).sort(
      (a, b) => stepMetadata[a].transitionedAt - stepMetadata[b].transitionedAt
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
                start={metadata.start}
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
