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
import { Cell, StructuredCell } from "./Cells";
import styled from "styled-components";

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
      case "PipelineProcessStartEvent":
      case "PipelineSuccessEvent":
      case "LogMessageEvent":
      case "PipelineStartEvent":
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
      <StructuredCell>
        <StepKeyColumn stepKey={"step" in node && node.step && node.step.key} />
        {this.renderStructuredContent()}
        <TimestampColumn time={"timestamp" in node && node.timestamp} />
      </StructuredCell>
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
        <StepKeyColumn stepKey={node.step && node.step.key} />
        <LevelContainer>{node.level}</LevelContainer>
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
const StepKeyColumn = (props: { stepKey: string | false | null }) => {
  const parts = (props.stepKey || "").replace(/\.compute$/, "").split(".");
  return (
    <StepKeyContainer>
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
    </StepKeyContainer>
  );
};

const TimestampColumn = (props: { time: string | false }) => (
  <TimestampContainer>
    {props.time &&
      new Date(Number(props.time))
        .toISOString()
        .replace("Z", "")
        .split("T")
        .pop()}
  </TimestampContainer>
);

const StepKeyContainer = styled.div`
  width: 250px;
  flex-shrink: 0;
`;

const TimestampContainer = styled.div`
  width: 100px;
  flex-shrink: 0;
  text-align: right;
  color: ${Colors.GRAY3};
`;

const LevelContainer = styled.div`
  width: 90px;
  flex-shrink: 0;
  color: ${Colors.GRAY3};
`;

const DefaultStructuredEvent = (props: { node: LogsRowStructuredFragment }) => (
  <>
    <LevelContainer />
    <span style={{ flex: 1 }}>{props.node.message}</span>
  </>
);

const PipelineProcessStartedEvent = (props: {
  node: LogsRowStructuredFragment_PipelineProcessStartedEvent;
}) => (
  <>
    <LevelContainer />
    {`Pipeline started `}
    <span style={{ flex: 1, color: Colors.GRAY3 }}>{`PID: ${
      props.node.processId
    }`}</span>
  </>
);

const DefaultFailureEvent = (props: {
  node:
    | LogsRowStructuredFragment_ExecutionStepFailureEvent
    | LogsRowStructuredFragment_PipelineInitFailureEvent;
}) => (
  <>
    <LevelContainer />
    <span style={{ flex: 1, color: Colors.RED3 }}>
      {`${props.node.error.message}\n${props.node.error.stack}`}
    </span>
  </>
);

const StepExpectationResultEvent = ({
  node
}: {
  node: LogsRowStructuredFragment_StepExpectationResultEvent;
}) => (
  <>
    <LevelContainer />
    {/* {events.steps[(node as any).step!.key].expectationResults.map((e, idx) => (
      <DisplayEvent event={e} key={`${idx}`} />
    ))} */}
  </>
);

const StepMaterializationEvent = ({
  node
}: {
  node: LogsRowStructuredFragment_StepMaterializationEvent;
}) => (
  <>
    <LevelContainer />
    {/* {events.steps[node.step!.key].materializations.map((e, idx) => (
      <DisplayEvent event={e} key={`${idx}`} />
    ))} */}
  </>
);

const DefaultStructuredEmptyEvent = ({
  node,
  message
}: {
  message: string;
  node: LogsRowStructuredFragment;
}) => (
  <>
    <LevelContainer />
    <span style={{ flex: 1 }}>{message}</span>
  </>
);

const ExecutionStepFailureEvent = ({
  node
}: {
  node: LogsRowStructuredFragment_ExecutionStepFailureEvent;
}) => (
  <>
    <LevelContainer />
    <span style={{ flex: 1 }}>
      {`Failed with error: \n${node.error.message}\n${node.error.stack}`}
    </span>
  </>
);

const ExecutionStepOutputEvent = ({
  node
}: {
  node: LogsRowStructuredFragment_ExecutionStepOutputEvent;
}) => (
  <>
    <LevelContainer>
      <Tag
        minimal={true}
        intent={node.typeCheck.success ? "success" : "warning"}
        style={{ marginRight: 4 }}
      >
        Output
      </Tag>
    </LevelContainer>
    <span style={{ flex: 1 }}>
      {node.outputName}: {styleValueRepr(node.valueRepr)}
    </span>
  </>
);
const ExecutionStepInputEvent = ({
  node
}: {
  node: LogsRowStructuredFragment_ExecutionStepInputEvent;
}) => (
  <>
    <LevelContainer>
      <Tag
        minimal={true}
        intent={node.typeCheck.success ? "success" : "warning"}
        style={{ marginRight: 4 }}
      >
        Input
      </Tag>
    </LevelContainer>
    <span style={{ flex: 1 }}>
      {node.inputName}: {styleValueRepr(node.valueRepr)}
    </span>
  </>
);
