import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { PipelineRunExecutionPlanFragment } from "./types/PipelineRunExecutionPlanFragment";
import { ExecutionPlanBox } from "./PipelineRunExecutionPlanBox";
import { IRunMetadataDict, IStepState } from "./RunMetadataProvider";

interface IPipelineRunExecutionPlanProps {
  run: PipelineRunExecutionPlanFragment;
  runMetadata: IRunMetadataDict;
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
            kind
          }
        }
      }
    `
  };

  render() {
    const {
      onApplyStepFilter,
      onShowStateDetails,
      runMetadata,
      run: { executionPlan }
    } = this.props;

    const stepsOrderedByTransitionTime = Object.keys(runMetadata.steps).sort(
      (a, b) =>
        runMetadata.steps[a].transitionedAt -
        runMetadata.steps[b].transitionedAt
    );

    let startDone = false;
    let startText = (
      <span>
        {`Process starting`}
        <AnimatedEllipsis />
      </span>
    );
    if (runMetadata.processId) {
      startText = (
        <span>
          {`Process (PID ${runMetadata.processId})`}
          <AnimatedEllipsis />
        </span>
      );
    }
    if (runMetadata.startedPipelineAt) {
      startDone = true;
      startText = (
        <span>
          {`Process (PID ${runMetadata.processId}) began pipeline execution`}
        </span>
      );
    }

    return (
      <ExecutionPlanContainer>
        <ExecutionPlanContainerInner>
          <ExecutionTimeline />
          <ExecutionTimelineMessage>
            <ExecutionTimelineDot completed={startDone} /> {startText}
          </ExecutionTimelineMessage>
          {executionPlan.steps.map(step => {
            const delay = stepsOrderedByTransitionTime.indexOf(step.name) * 100;
            const metadata = runMetadata.steps[step.name] || {
              state: IStepState.WAITING
            };

            return (
              <ExecutionPlanBox
                key={step.name}
                state={metadata.state}
                start={metadata.start}
                elapsed={metadata.elapsed}
                name={step.name}
                materializations={metadata.materializations}
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
  bottom: 15px;
`;

const ExecutionTimelineDot = styled.div<{ completed: boolean }>`
  display: inline-block;
  width: 11px;
  height: 11px;
  border-radius: 5.5px;
  margin-right: 8px;
  background: #232b2f;
  border: 1px solid
    ${({ completed }) => (completed ? Colors.LIGHT_GRAY2 : Colors.GRAY1)};
  margin-left: 18px;
  flex-shrink: 0;
`;

const AnimatedEllipsis = () => {
  return (
    <AnimatedEllipsisContainer>
      <span>.</span>
      <span>.</span>
      <span>.</span>
    </AnimatedEllipsisContainer>
  );
};

const AnimatedEllipsisContainer = styled.span`
  @keyframes ellipsis-dot {
    0% {
      opacity: 0;
    }
    50% {
      opacity: 1;
    }
    100% {
      opacity: 0;
    }
  }
  span {
    opacity: 0;
    animation: ellipsis-dot 1s infinite;
  }
  span:nth-child(1) {
    animation-delay: 0s;
  }
  span:nth-child(2) {
    animation-delay: 0.1s;
  }
  span:nth-child(3) {
    animation-delay: 0.2s;
  }
`;
