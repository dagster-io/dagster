import * as React from "react";
import { Tag } from "@blueprintjs/core";
import { LogsScrollingTableMessageFragment } from "./types/LogsScrollingTableMessageFragment";

import { DisplayEvent } from "../plan/DisplayEvent";
import { extractMetadataFromLogs } from "../RunMetadataProvider";
import { HighlightedCodeBlock } from "../HighlightedCodeBlock";
import gql from "graphql-tag";
import { LogsRowStructuredFragment } from "./types/LogsRowStructuredFragment";
import { LogsRowUnstructuredFragment } from "./types/LogsRowUnstructuredFragment";

function styleValueRepr(repr: string) {
  if (repr.startsWith("DataFrame")) {
    const content = repr.split("[")[1].split("]")[0];
    const cells: React.ReactNode[] = [];
    content.split(",").forEach(el => {
      const [key, val] = el.split(":");
      cells.push(
        <React.Fragment key={key}>
          <span style={{ color: "#bd4e08" }}>{key}:</span>
          <span style={{ color: "purple" }}>{val}</span>,
        </React.Fragment>
      );
    });
    return <span>DataFrame: [{cells}]</span>;
  }
  if (repr.startsWith("<dagster")) {
    return <span style={{ color: "#bd4e08" }}>{repr}</span>;
  }
  if (repr.startsWith("{'")) {
    return (
      <HighlightedCodeBlock
        value={JSON.stringify(
          JSON.parse(repr.replace(/"/g, "'").replace(/'/g, '"')),
          null,
          2
        )}
      />
    );
  }
  return repr;
}

export class Structured extends React.Component<{
  node: LogsRowStructuredFragment;
}> {
  static fragments = {
    LogsRowStructuredFragment: gql`
      fragment MetadataEntryFragment on EventMetadataEntry {
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
      fragment LogsRowStructuredFragment on PipelineRunEvent {
        __typename
        ... on PipelineProcessStartedEvent {
          processId
        }
        ... on StepMaterializationEvent {
          step {
            key
          }
          materialization {
            label
            description
            metadataEntries {
              ...MetadataEntryFragment
            }
          }
        }
        ... on PipelineInitFailureEvent {
          error {
            stack
            message
          }
        }
        ... on ExecutionStepFailureEvent {
          message
          level
          step {
            key
          }
          error {
            stack
            message
          }
        }
        ... on ExecutionStepInputEvent {
          inputName
          valueRepr
          typeCheck {
            label
            description
            success
            metadataEntries {
              label
              description
            }
          }
        }
        ... on ExecutionStepOutputEvent {
          outputName
          valueRepr
          typeCheck {
            label
            description
            success
            metadataEntries {
              label
              description
            }
          }
        }
        ... on StepExpectationResultEvent {
          expectationResult {
            success
            label
            description
            metadataEntries {
              ...MetadataEntryFragment
            }
          }
        }
      }
    `
  };

  render() {
    const { node } = this.props;
    if (node.__typename === "StepExpectationResultEvent") {
      const events = extractMetadataFromLogs([node as any]);
      return (
        <div>
          {events.steps[(node as any).step!.key].expectationResults.map(
            (e, idx) => (
              <DisplayEvent event={e} key={`${idx}`} />
            )
          )}
        </div>
      );
    }
    if (node.__typename === "StepMaterializationEvent") {
      const events = extractMetadataFromLogs([node as any]);
      return (
        <div>
          {events.steps[node.step!.key].materializations.map((e, idx) => (
            <DisplayEvent event={e} key={`${idx}`} />
          ))}
        </div>
      );
    }
    if (node.__typename === "ExecutionStepStartEvent") {
      return <span>Started</span>;
    }
    if (node.__typename === "ExecutionStepFailureEvent") {
      return (
        <span>{`Failed with error: \n${node.error.message}\n${
          node.error.stack
        }`}</span>
      );
    }
    if (node.__typename === "ExecutionStepSkippedEvent") {
      return <span>Skipped</span>;
    }
    if (node.__typename === "ExecutionStepOutputEvent") {
      return (
        <span>
          <Tag
            minimal={true}
            intent={node.typeCheck.success ? "success" : "warning"}
            style={{ marginRight: 4 }}
          >
            Output
          </Tag>
          {node.outputName}: {styleValueRepr(node.valueRepr)}
        </span>
      );
    }
    if (node.__typename === "ExecutionStepInputEvent") {
      return (
        <span>
          <Tag
            minimal={true}
            intent={node.typeCheck.success ? "success" : "warning"}
            style={{ marginRight: 4 }}
          >
            Input
          </Tag>
          {node.inputName}: {styleValueRepr(node.valueRepr)}
        </span>
      );
    }
    if (node.__typename === "ExecutionStepSuccessEvent") {
      return <span>Success</span>;
    }
    return <span>{node.__typename}</span>;
  }
}

export class Unstructured extends React.Component<{
  node: LogsRowUnstructuredFragment;
}> {
  static fragments = {
    LogsRowUnstructuredFragment: gql`
      fragment LogsRowUnstructuredFragment on PipelineRunEvent {
        __typename
        ... on MessageEvent {
          message
          timestamp
          level
          step {
            key
          }
        }
      }
    `
  };

  render() {
    const { node } = this.props;

    return <span>{node.message}</span>;
  }
}
