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
  icon:
    | "dot-success"
    | "dot-failure"
    | "dot-pending"
    | "file"
    | "link"
    | "none";
  text: string;
  items: {
    text: string; // shown in gray on the left
    action: "open-in-tab" | "copy" | "show-in-modal" | "none";
    actionText: string; // shown after `text`, optionally with a click action
    actionValue: string; // value passed to the click action
  }[];
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
        metadata.steps[name] = {
          state: IStepState.SKIPPED,
          transitionedAt: timestamp,
          displayEvents: []
        };
      } else if (log.__typename === "StepMaterializationEvent") {
        metadata.steps[name] = produce(metadata.steps[name] || {}, step => {
          step.displayEvents.push({
            icon: "link",
            text: "Materialization",
            items: [
              {
                text: (log.materialization.path || "").split("/").pop()!,
                actionText: "[Copy Path]",
                action: "copy",
                actionValue: log.materialization.path || ""
              }
            ]
          });
        });
      } else if (log.__typename == "StepExpectationResultEvent") {
        metadata.steps[name] = produce(metadata.steps[name] || {}, step => {
          step.displayEvents.push({
            icon: log.expectationResult.success ? "dot-success" : "dot-failure",
            text: log.expectationResult.name
              ? "Expectation: " + log.expectationResult.name
              : "Expectation",
            items: log.expectationResult.resultMetadataJsonString
              ? [
                  {
                    text: "",
                    actionText: "[Show Metadata]",
                    action: "show-in-modal",
                    // take JSON string, parse, and then pretty print
                    actionValue: JSON.stringify(
                      JSON.parse(
                        log.expectationResult.resultMetadataJsonString
                      ),
                      null,
                      2
                    )
                  }
                ]
              : []
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
        ... on StepExpectationResultEvent {
          expectationResult {
            success
            name
            resultMetadataJsonString
          }
        }
      }
    `
  };

  render() {
    return this.props.children(extractMetadataFromLogs(this.props.logs));
  }
}
