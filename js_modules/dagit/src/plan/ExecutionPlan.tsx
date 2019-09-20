import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { ExecutionPlanFragment } from "./types/ExecutionPlanFragment";
import { ExecutionPlanBox } from "./ExecutionPlanBox";
import { AnimatedEllipsis } from "./AnimatedEllipsis";
import { ExecutionPlanHiddenStepsBox } from "./ExecutionPlanHiddenStepsBox";
import {
  IRunMetadataDict,
  IStepState,
  IStepMetadata
} from "../RunMetadataProvider";
import { RunHistoryRunFragment } from "../runs/types/RunHistoryRunFragment";
import { formatElapsedTime } from "../Util";

export interface IExecutionPlanProps {
  executionPlan: ExecutionPlanFragment;
  stepKeysToExecute?: (string | null)[] | null;
  runMetadata?: IRunMetadataDict;
  run?: RunHistoryRunFragment;
  onApplyStepFilter?: (step: string) => void;
  onShowStateDetails?: (step: string) => void;
  onReexecuteStep?: (step: string) => void;
}

const EMPTY_RUN_METADATA: IRunMetadataDict = {
  steps: {}
};

const EMPTY_STEP_METADATA: IStepMetadata = {
  state: IStepState.WAITING,
  start: undefined,
  elapsed: undefined,
  transitionedAt: 0,
  expectationResults: [],
  materializations: []
};

export class ExecutionPlan extends React.PureComponent<IExecutionPlanProps> {
  static fragments = {
    ExecutionPlanFragment: gql`
      fragment ExecutionPlanFragment on ExecutionPlan {
        steps {
          key
          kind
        }
        artifactsPersisted
      }
    `
  };

  renderSkippedSteps(skippedCount: number) {
    if (skippedCount > 0) {
      return <ExecutionPlanHiddenStepsBox numberStepsSkipped={skippedCount} />;
    }

    return null;
  }

  render() {
    const haveRun = !!this.props.runMetadata;
    const {
      onApplyStepFilter,
      onShowStateDetails,
      onReexecuteStep,
      runMetadata = EMPTY_RUN_METADATA,
      executionPlan,
      stepKeysToExecute,
      run
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
          {`Loading`}
          <AnimatedEllipsis />
        </span>
      );
      if (runMetadata.startingProcessAt) {
        startText = (
          <span>
            {`Process starting`}
            <AnimatedEllipsis />
          </span>
        );
      }
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
      } else if (runMetadata.initFailed) {
        startDone = true;
        startText = (
          <span>
            {`Process (PID ${runMetadata.processId}) pipeline initialization failed!`}
          </span>
        );
      }
      if (
        run &&
        run.pipeline &&
        run.pipeline.__typename === "UnknownPipeline"
      ) {
        startDone = true;
        startText = (
          <span>
            Could not load execution plan for pipeline {run.pipeline.name}.
          </span>
        );
      }
    }

    // Keep track of skipped steps that were not part of the current run
    let stepsSkippedCount = 0;
    let prevSkippedCount = 0;

    return (
      <ExecutionPlanContainer>
        <ExecutionPlanContainerInner>
          <ExecutionTimeline />
          <ExecutionTimelineMessage>
            <ExecutionTimelineDot completed={startDone} /> {startText}
          </ExecutionTimelineMessage>
          {executionPlan &&
            executionPlan.steps.map(step => {
              const delay =
                stepsOrderedByTransitionTime.indexOf(step.key) * 100;
              const metadata =
                runMetadata.steps[step.key] || EMPTY_STEP_METADATA;

              // If stepKeysToExecute is null, then all steps are being run
              const isStepPartOfRun =
                !stepKeysToExecute || stepKeysToExecute.indexOf(step.key) > -1;

              if (!isStepPartOfRun) {
                stepsSkippedCount++;
                return null;
              } else {
                prevSkippedCount = stepsSkippedCount;
                stepsSkippedCount = 0;
              }

              return (
                <div key={step.key}>
                  {this.renderSkippedSteps(prevSkippedCount)}
                  <ExecutionPlanBox
                    state={metadata.state}
                    start={metadata.start}
                    elapsed={metadata.elapsed}
                    key={step.key}
                    stepKey={step.key}
                    expectationResults={metadata.expectationResults}
                    materializations={metadata.materializations}
                    onShowStateDetails={onShowStateDetails}
                    onApplyStepFilter={onApplyStepFilter}
                    onReexecuteStep={onReexecuteStep}
                    executionArtifactsPersisted={
                      executionPlan.artifactsPersisted
                    }
                    delay={delay}
                  />
                </div>
              );
            })}
          {this.renderSkippedSteps(stepsSkippedCount)}
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
