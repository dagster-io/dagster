import * as React from "react";
import produce from "immer";
import gql from "graphql-tag";

import { RunMetadataProviderMessageFragment } from "./types/RunMetadataProviderMessageFragment";
import { TempMetadataEntryFragment } from "./types/TempMetadataEntryFragment";

export enum IStepState {
  WAITING = "waiting",
  RUNNING = "running",
  SUCCEEDED = "succeeded",
  SKIPPED = "skipped",
  FAILED = "failed"
}

export enum IExpectationResultStatus {
  PASSED = "Passed",
  FAILED = "Failed"
}

export enum IStepDisplayIconType {
  SUCCESS = "dot-success",
  FAILURE = "dot-failure",
  PENDING = "dot-pending",
  FILE = "file",
  LINK = "link",
  NONE = "none"
}

export enum IStepDisplayActionType {
  OPEN_IN_TAB = "open-in-tab",
  COPY = "copy",
  SHOW_IN_MODAL = "show-in-modal",
  NONE = "none"
}

interface IDisplayEventItem {
  text: string; // shown in gray on the left
  action: IStepDisplayActionType;
  actionText: string; // shown after `text`, optionally with a click action
  actionValue: string; // value passed to the click action
}

export interface IStepDisplayEvent {
  icon: IStepDisplayIconType;
  text: string;
  items: IDisplayEventItem[];
}

export interface IExpectationResult extends IStepDisplayEvent {
  status: IExpectationResultStatus;
}

export interface IMaterialization extends IStepDisplayEvent {}

export interface IStepMetadata {
  state: IStepState;
  start?: number;
  elapsed?: number;
  transitionedAt: number;
  expectationResults: IExpectationResult[];
  materializations: IMaterialization[];
}

export interface IRunMetadataDict {
  startingProcessAt?: number;
  startedProcessAt?: number;
  startedPipelineAt?: number;
  exitedAt?: number;
  processId?: number;
  initFailed?: boolean;
  steps: {
    [stepKey: string]: IStepMetadata;
  };
}

function itemsForMetadataEntries(
  metadataEntries: TempMetadataEntryFragment[]
): IDisplayEventItem[] {
  const items = [];
  for (const metadataEntry of metadataEntries) {
    switch (metadataEntry.__typename) {
      case "EventPathMetadataEntry":
        items.push({
          text: metadataEntry.label,
          actionText: "[Copy Path]",
          action: IStepDisplayActionType.COPY,
          actionValue: metadataEntry.path
        });
        break;
      case "EventJsonMetadataEntry":
        items.push({
          text: metadataEntry.label,
          actionText: "[Show Metadata]",
          action: IStepDisplayActionType.SHOW_IN_MODAL,
          // take JSON string, parse, and then pretty print
          actionValue: JSON.stringify(
            JSON.parse(metadataEntry.jsonString),
            null,
            2
          )
        });

        break;
      case "EventUrlMetadataEntry":
        items.push({
          text: metadataEntry.label,
          actionText: "[Open URL]",
          action: IStepDisplayActionType.OPEN_IN_TAB,
          actionValue: metadataEntry.url
        });

        break;
      case "EventTextMetadataEntry":
        items.push({
          text: metadataEntry.label,
          actionText: metadataEntry.text,
          action: IStepDisplayActionType.NONE,
          actionValue: ""
        });

        break;
    }
  }

  return items;
}

export function extractMetadataFromLogs(
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
      const stepKey = log.step.key;
      const timestamp = Number.parseInt(log.timestamp, 10);

      if (log.__typename === "ExecutionStepStartEvent") {
        metadata.steps[stepKey] = {
          state: IStepState.RUNNING,
          start: timestamp,
          transitionedAt: timestamp,
          expectationResults: [],
          materializations: []
        };
      } else if (log.__typename === "ExecutionStepSuccessEvent") {
        metadata.steps[stepKey] = produce(
          metadata.steps[stepKey] || {},
          step => {
            step.state = IStepState.SUCCEEDED;
            if (step.start) {
              step.transitionedAt = timestamp;
              step.elapsed = timestamp - step.start;
            }
          }
        );
      } else if (log.__typename === "ExecutionStepSkippedEvent") {
        metadata.steps[stepKey] = {
          state: IStepState.SKIPPED,
          transitionedAt: timestamp,
          expectationResults: [],
          materializations: []
        };
      } else if (log.__typename === "StepMaterializationEvent") {
        metadata.steps[stepKey] = produce(
          metadata.steps[stepKey] || {
            expectationResults: [],
            materializations: []
          },
          step => {
            step.materializations.push({
              icon: IStepDisplayIconType.LINK,
              text: log.materialization.label || "Materialization",
              items: itemsForMetadataEntries(
                log.materialization.metadataEntries
              )
            });
          }
        );
      } else if (log.__typename == "StepExpectationResultEvent") {
        metadata.steps[stepKey] = produce(
          metadata.steps[stepKey] || {
            expectationResults: [],
            materializations: []
          },
          step => {
            step.expectationResults.push({
              status: log.expectationResult.success
                ? IExpectationResultStatus.PASSED
                : IExpectationResultStatus.FAILED,
              icon: log.expectationResult.success
                ? IStepDisplayIconType.SUCCESS
                : IStepDisplayIconType.FAILURE,
              text: log.expectationResult.label,
              items: itemsForMetadataEntries(
                log.expectationResult.metadataEntries
              )
            });
          }
        );
      } else if (log.__typename === "ExecutionStepFailureEvent") {
        metadata.steps[stepKey] = produce(
          metadata.steps[stepKey] || {},
          step => {
            step.state = IStepState.FAILED;
            if (step.start) {
              step.transitionedAt = timestamp;
              step.elapsed = timestamp - step.start;
            }
          }
        );
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
      fragment TempMetadataEntryFragment on EventMetadataEntry {
        label
        description
        ... on EventPathMetadataEntry {
          path
        }
        ... on EventJsonMetadataEntry {
          jsonString
        }
        ... on EventUrlMetadataEntry {
          url
        }
        ... on EventTextMetadataEntry {
          text
        }
      }

      fragment RunMetadataProviderMessageFragment on PipelineRunEvent {
        __typename
        ... on MessageEvent {
          message
          timestamp
          step {
            key
          }
        }
        ... on PipelineProcessStartedEvent {
          processId
        }
        ... on PipelineProcessStartEvent {
          pipelineName
          runId
        }
        ... on StepMaterializationEvent {
          step {
            key
          }
          materialization {
            label
            description
            metadataEntries {
              ...TempMetadataEntryFragment
            }
          }
        }
        ... on StepExpectationResultEvent {
          expectationResult {
            success
            label
            description
            metadataEntries {
              ...TempMetadataEntryFragment
            }
          }
        }
      }
    `
  };

  render() {
    return this.props.children(extractMetadataFromLogs(this.props.logs));
  }
}
