import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { ExecutionPlanFragment } from "./types/ExecutionPlanFragment";
import { ExecutionPlanBox } from "./ExecutionPlanBox";
import {
  IRunMetadataDict,
  IStepState,
  IStepMetadata
} from "./RunMetadataProvider";
import { formatElapsedTime } from "./Util";

interface IExecutionPlanProps {
  executionPlan: ExecutionPlanFragment;
  runMetadata?: IRunMetadataDict;
  onApplyStepFilter?: (step: string) => void;
  onShowStateDetails?: (step: string) => void;
}

const EMPTY_RUN_METADATA: IRunMetadataDict = {
  steps: {}
};

const EMPTY_STEP_METADATA: IStepMetadata = {
  state: IStepState.WAITING,
  start: undefined,
  elapsed: undefined,
  transitionedAt: 0,
  materializations: []
};

export default class ExecutionPlan extends React.PureComponent<
  IExecutionPlanProps
> {
  static fragments = {
    ExecutionPlanFragment: gql`
      fragment ExecutionPlanFragment on ExecutionPlan {
        steps {
          name
          solid {
            name
          }
          kind
        }
      }
    `
  };

  render() {
    const haveRun = !!this.props.runMetadata;
    const {
      onApplyStepFilter,
      onShowStateDetails,
      runMetadata = EMPTY_RUN_METADATA,
      executionPlan
    } = this.props;

    const stepsOrderedByTransitionTime = Object.keys(runMetadata.steps).sort(
      (a, b) =>
        runMetadata.steps[a].transitionedAt -
        runMetadata.steps[b].transitionedAt
    );

    let startDone = false;
    let startText = null;

    if (haveRun) {
      startText = (
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
            const metadata =
              runMetadata.steps[step.name] || EMPTY_STEP_METADATA;

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
          {runMetadata.exitedAt && runMetadata.startedProcessAt && (
            <ExecutionTimelineMessage>
              <ExecutionTimelineDot completed={startDone} />
              <span>
                {`Process exited in ${formatElapsedTime(
                  runMetadata.exitedAt - runMetadata.startedProcessAt
                )}`}
              </span>
            </ExecutionTimelineMessage>
          )}
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
  margin-top: 10px;
  position: relative;
  margin-bottom: 10px;
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
  margin-top: 3px;
  margin-bottom: 3px;
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
