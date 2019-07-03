import * as React from "react";
import gql from "graphql-tag";

import { HighlightedCodeBlock } from "../HighlightedCodeBlock";
import {
  LogsRowStructuredFragment,
  LogsRowStructuredFragment_ExecutionStepFailureEvent,
  LogsRowStructuredFragment_StepMaterializationEvent,
  LogsRowStructuredFragment_ExecutionStepOutputEvent,
  LogsRowStructuredFragment_ExecutionStepInputEvent,
  LogsRowStructuredFragment_StepExpectationResultEvent,
  LogsRowStructuredFragment_PipelineProcessStartedEvent,
  LogsRowStructuredFragment_PipelineInitFailureEvent
} from "./types/LogsRowStructuredFragment";
import { LogsRowUnstructuredFragment } from "./types/LogsRowUnstructuredFragment";
import { Tag, Colors } from "@blueprintjs/core";
import { Cell } from "./Cells";
import { LogLevel } from "./LogsFilterProvider";

function assertUnreachable(x: never): never {
  throw new Error("Didn't expect to get here");
}

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
        ... on MessageEvent {
          message
          timestamp
          level
          step {
            key
          }
        }
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

  renderStructuredContent() {
    const { node } = this.props;

    switch (node.__typename) {
      // Errors
      case "ExecutionStepFailureEvent":
        return <DefaultFailureEvent node={node} />;
      case "PipelineInitFailureEvent":
        return <DefaultFailureEvent node={node} />;

      // Using custom messages
      case "ExecutionStepStartEvent":
        return <DefaultStructuredEmptyEvent node={node} message="Started" />;
      case "ExecutionStepSkippedEvent":
        return <DefaultStructuredEmptyEvent node={node} message="Skipped" />;
      case "ExecutionStepSuccessEvent":
        return <DefaultStructuredEmptyEvent node={node} message="Success" />;

      // Using custom renderers
      case "ExecutionStepInputEvent":
        return <ExecutionStepInputEvent node={node} />;
      case "ExecutionStepOutputEvent":
        return <ExecutionStepOutputEvent node={node} />;
      case "PipelineProcessStartedEvent":
        return <PipelineProcessStartedEvent node={node} />;
      case "StepExpectationResultEvent":
        return <StepExpectationResultEvent node={node} />;
      case "StepMaterializationEvent":
        return <StepMaterializationEvent node={node} />;

      // Using server-provided messages
      case "PipelineFailureEvent":
        return <DefaultStructuredEvent node={node} />;
      case "PipelineProcessStartEvent":
        return <DefaultStructuredEvent node={node} />;
      case "PipelineStartEvent":
        return <DefaultStructuredEvent node={node} />;
      case "PipelineSuccessEvent":
        return <DefaultStructuredEvent node={node} />;
      case "LogMessageEvent":
        return <DefaultStructuredEvent node={node} />;
      default:
        // This allows us to check that the switch is exhaustive because the union type should
        // have been narrowed following each successive case to `never` at this point.
        return assertUnreachable(node);
    }
  }

  render() {
    const { node } = this.props;

    return (
      <Cell level={LogLevel.EVENT}>
        <StepColumn stepKey={"step" in node && node.step && node.step.key} />
        <span style={{ flex: 1 }}>{this.renderStructuredContent()}</span>
        <TimestampColumn time={"timestamp" in node && node.timestamp} />
      </Cell>
    );
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
    return (
      <Cell level={node.level}>
        <StepColumn stepKey={node.step && node.step.key} />
        <span style={{ width: 90, flexShrink: 0, color: Colors.GRAY3 }}>
          {node.level}
        </span>
        <span style={{ flex: 1 }}>{node.message}</span>
        <TimestampColumn time={node.timestamp} />
      </Cell>
    );
  }
}

// Structured Content Renderers

// Renders the left column with the step key broken into hierarchical components.
// Manually implements middle text truncation since we can count on monospace font
// rendering being fairly consistent.
//
const StepColumn = (props: { stepKey: string | false | null }) => {
  const parts = (props.stepKey || "").replace(/\.compute$/, "").split(".");
  return (
    <div style={{ width: 250, flexShrink: 0 }}>
      {parts.map((p, idx) => (
        <div
          key={idx}
          style={{
            paddingLeft: Math.max(0, idx * 15 - 9),
            paddingRight: 15,
            fontWeight: idx === parts.length - 1 ? 600 : 300
          }}
        >
          {idx > 0 ? "↳" : ""}
          {p.length > 30 - idx * 2
            ? `${p.substr(0, 16 - idx * 2)}…${p.substr(p.length - 14)}`
            : p}
        </div>
      ))}
    </div>
  );
};

const TimestampColumn = (props: { time: string | false }) => (
  <div
    style={{
      width: 100,
      flexShrink: 0,
      textAlign: "right",
      color: Colors.GRAY3
    }}
  >
    {props.time &&
      new Date(Number(props.time))
        .toISOString()
        .replace("Z", "")
        .split("T")
        .pop()}
  </div>
);

const DefaultStructuredEvent = (props: { node: LogsRowStructuredFragment }) => (
  <div>{props.node.message}</div>
);

const PipelineProcessStartedEvent = (props: {
  node: LogsRowStructuredFragment_PipelineProcessStartedEvent;
}) => (
  <div>
    {`Pipeline started `}
    <span style={{ color: Colors.GRAY3 }}>{`PID: ${
      props.node.processId
    }`}</span>
  </div>
);

const DefaultFailureEvent = (props: {
  node:
    | LogsRowStructuredFragment_ExecutionStepFailureEvent
    | LogsRowStructuredFragment_PipelineInitFailureEvent;
}) => (
  <div style={{ color: Colors.RED3 }}>{`${props.node.error.message}\n${
    props.node.error.stack
  }`}</div>
);

const StepExpectationResultEvent = ({
  node
}: {
  node: LogsRowStructuredFragment_StepExpectationResultEvent;
}) => (
  <div>
    {/* {events.steps[(node as any).step!.key].expectationResults.map((e, idx) => (
      <DisplayEvent event={e} key={`${idx}`} />
    ))} */}
  </div>
);

const StepMaterializationEvent = ({
  node
}: {
  node: LogsRowStructuredFragment_StepMaterializationEvent;
}) => (
  <div>
    {/* {events.steps[node.step!.key].materializations.map((e, idx) => (
      <DisplayEvent event={e} key={`${idx}`} />
    ))} */}
  </div>
);

const DefaultStructuredEmptyEvent = ({
  node,
  message
}: {
  message: string;
  node: LogsRowStructuredFragment;
}) => <span>{message}</span>;

const ExecutionStepFailureEvent = ({
  node
}: {
  node: LogsRowStructuredFragment_ExecutionStepFailureEvent;
}) => (
  <span>{`Failed with error: \n${node.error.message}\n${
    node.error.stack
  }`}</span>
);

const ExecutionStepOutputEvent = ({
  node
}: {
  node: LogsRowStructuredFragment_ExecutionStepOutputEvent;
}) => (
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
const ExecutionStepInputEvent = ({
  node
}: {
  node: LogsRowStructuredFragment_ExecutionStepInputEvent;
}) => (
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
