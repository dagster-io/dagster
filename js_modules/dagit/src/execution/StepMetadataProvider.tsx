import * as React from "react";
import produce from "immer";
import gql from "graphql-tag";

import { StepMetadataProviderMessageFragment } from "./types/StepMetadataProviderMessageFragment";

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

export interface IStepMetadataDict {
  [stepName: string]: IStepMetadata;
}

function extractMetadataFromLogs(
  logs: StepMetadataProviderMessageFragment[]
): IStepMetadataDict {
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

interface IStepMetadataProviderProps {
  logs: StepMetadataProviderMessageFragment[];
  children: (metadata: IStepMetadataDict) => React.ReactElement<any>;
}

export default class StepMetadataProvider extends React.Component<
  IStepMetadataProviderProps
> {
  static fragments = {
    StepMetadataProviderMessageFragment: gql`
      fragment StepMetadataProviderMessageFragment on PipelineRunEvent {
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
    return this.props.children(extractMetadataFromLogs(this.props.logs));
  }
}
