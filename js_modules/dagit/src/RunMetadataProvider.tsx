import * as React from "react";
import produce from "immer";
import gql from "graphql-tag";

import { RunMetadataProviderMessageFragment } from "./types/RunMetadataProviderMessageFragment";

export enum IStepState {
  WAITING = "waiting",
  RUNNING = "running",
  SUCCEEDED = "succeeded",
  SKIPPED = "skipped",
  FAILED = "failed"
}

export interface IStepDisplayEvent {
  type: "materialization" | "intermediate" | "other";
  key: string | null;
  value: string | null;
  hidden: boolean; // true to place inside disclosure triangle
}

export interface IStepMetadata {
  state: IStepState;
  start?: number;
  elapsed?: number;
  transitionedAt: number;
  displayEvents: IStepDisplayEvent[];
}

export interface IRunMetadataDict {
  startingProcessAt?: number;
  startedProcessAt?: number;
  startedPipelineAt?: number;
  exitedAt?: number;
  processId?: number;
  initFailed?: boolean;
  steps: {
    [stepName: string]: IStepMetadata;
  };
}

function extractMetadataFromLogs(
  logs: RunMetadataProviderMessageFragment[]
): IRunMetadataDict {
  const metadata: IRunMetadataDict = {
    steps: {}
  };

  logs.forEach(log => {
    if (log.__typename === "PipelineProcessStartEvent") {
      metadata.startingProcessAt = Number.parseInt(log.timestamp);
    }
    if (log.__typename === "PipelineProcessStartedEvent") {
      metadata.startedProcessAt = Number.parseInt(log.timestamp);
      metadata.processId = log.processId;
    }
    if (log.__typename === "PipelineStartEvent") {
      metadata.startedPipelineAt = Number.parseInt(log.timestamp);
    }
    if (log.__typename === "PipelineInitFailureEvent") {
      metadata.initFailed = true;
      metadata.exitedAt = Number.parseInt(log.timestamp);
    }
    if (
      log.__typename === "PipelineFailureEvent" ||
      log.__typename === "PipelineSuccessEvent"
    ) {
      metadata.exitedAt = Number.parseInt(log.timestamp);
    }

    if (log.step) {
      const name = log.step.name;
      const timestamp = Number.parseInt(log.timestamp, 10);

      if (log.__typename === "ExecutionStepStartEvent") {
        metadata.steps[name] = {
          state: IStepState.RUNNING,
          start: timestamp,
          transitionedAt: timestamp,
          displayEvents: []
        };
      } else if (log.__typename === "ExecutionStepSuccessEvent") {
        metadata.steps[name] = produce(metadata.steps[name] || {}, step => {
          step.state = IStepState.SUCCEEDED;
          if (step.start) {
            step.transitionedAt = timestamp;
            step.elapsed = timestamp - step.start;
          }
        });
      } else if (log.__typename === "ExecutionStepSkippedEvent") {
        metadata.steps[name] = produce(metadata.steps[name] || {}, step => {
          step.state = IStepState.SKIPPED;
        });
      } else if (log.__typename === "StepMaterializationEvent") {
        metadata.steps[name] = produce(metadata.steps[name] || {}, step => {
          step.displayEvents.push({
            type: "materialization",
            key: log.materialization.description,
            value: log.materialization.path,
            hidden: false
          });
          step.displayEvents.push({
            type: "materialization",
            key: "plan_type",
            value: "complex",
            hidden: true
          });
          step.displayEvents.push({
            type: "materialization",
            key: "conversion_speed_seed",
            value: "123.1511",
            hidden: true
          });
        });
      } else if (log.__typename === "ExecutionStepFailureEvent") {
        metadata.steps[name] = produce(metadata.steps[name] || {}, step => {
          step.state = IStepState.FAILED;
          if (step.start) {
            step.transitionedAt = timestamp;
            step.elapsed = timestamp - step.start;
          }
        });
      }
    }
  });
  return metadata;
}

interface IRunMetadataProviderProps {
  logs: RunMetadataProviderMessageFragment[];
  children: (metadata: IRunMetadataDict) => React.ReactElement<any>;
}

export default class RunMetadataProvider extends React.Component<
  IRunMetadataProviderProps
> {
  static fragments = {
    RunMetadataProviderMessageFragment: gql`
      fragment RunMetadataProviderMessageFragment on PipelineRunEvent {
        __typename
        ... on MessageEvent {
          message
          timestamp
          step {
            name
          }
        }
        ... on PipelineProcessStartedEvent {
          processId
        }
        ... on StepMaterializationEvent {
          step {
            name
          }
          materialization {
            path
            description
          }
        }
      }
    `
  };

  render() {
    return this.props.children(extractMetadataFromLogs(this.props.logs));
  }
}
