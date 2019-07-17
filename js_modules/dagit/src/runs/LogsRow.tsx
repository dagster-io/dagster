import * as React from "react";
import gql from "graphql-tag";
import { LogLevel } from "../types/globalTypes";
import { Tag, Colors } from "@blueprintjs/core";

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
import {
  Row,
  StructuredContent,
  LabelColumn,
  LevelTagColumn,
  StepKeyColumn,
  TimestampColumn
} from "./LogsRowComponents";
import { MetadataEntries, MetadataEntry } from "./MetadataEntry";
import { assertUnreachable } from "../Util";
import { TypeName } from "../TypeWithTooltip";

export class Structured extends React.Component<{
  node: LogsRowStructuredFragment;
}> {
  static fragments = {
    LogsRowStructuredFragment: gql`
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
          step {
            inputs {
              name
              type {
                displayName
                description
              }
            }
          }
          typeCheck {
            label
            description
            success
            metadataEntries {
              ...MetadataEntryFragment
            }
          }
        }
        ... on ExecutionStepOutputEvent {
          outputName
          step {
            outputs {
              name
              type {
                displayName
                description
              }
            }
          }
          typeCheck {
            label
            description
            success
            metadataEntries {
              ...MetadataEntryFragment
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
      ${MetadataEntry.fragments.MetadataEntryFragment}
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
        return (
          <DefaultStructuredEvent
            node={node}
            level={<Tag minimal={true}>Step Start</Tag>}
          />
        );
      case "ExecutionStepSkippedEvent":
        return (
          <DefaultStructuredEvent
            node={node}
            level={<Tag minimal={true}>Skipped</Tag>}
          />
        );
      case "ExecutionStepSuccessEvent":
        return (
          <DefaultStructuredEvent
            node={node}
            level={<Tag minimal={true}>Step Finished</Tag>}
          />
        );

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
      <Row level={LogLevel.INFO}>
        <StepKeyColumn stepKey={"step" in node && node.step && node.step.key} />
        <StructuredContent>{this.renderStructuredContent()}</StructuredContent>
        <TimestampColumn time={"timestamp" in node && node.timestamp} />
      </Row>
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
      <Row level={node.level}>
        <StepKeyColumn stepKey={node.step && node.step.key} />
        <LevelTagColumn>{node.level}</LevelTagColumn>
        <LabelColumn />
        <span style={{ flex: 1 }}>{node.message}</span>
        <TimestampColumn time={node.timestamp} />
      </Row>
    );
  }
}

// Structured Content Renderers

const DefaultStructuredEvent: React.FunctionComponent<{
  node: LogsRowStructuredFragment;
  level?: React.ReactNode;
}> = ({ node, level }) => (
  <>
    <LevelTagColumn>{level}</LevelTagColumn>
    <LabelColumn />
    <span style={{ flex: 1 }}>{node.message}</span>
  </>
);

const PipelineProcessStartedEvent: React.FunctionComponent<{
  node: LogsRowStructuredFragment_PipelineProcessStartedEvent;
}> = ({ node }) => (
  <>
    <LevelTagColumn>
      <Tag minimal={true}>Started</Tag>
    </LevelTagColumn>
    <LabelColumn />
    {`Pipeline started `}
    <span style={{ flex: 1, color: Colors.GRAY3 }}>
      {`PID: ${node.processId}`}
    </span>
  </>
);

const DefaultFailureEvent: React.FunctionComponent<{
  node:
    | LogsRowStructuredFragment_ExecutionStepFailureEvent
    | LogsRowStructuredFragment_PipelineInitFailureEvent;
}> = ({ node }) => (
  <>
    <LevelTagColumn>
      <Tag minimal={true} intent="danger">
        Failed
      </Tag>
    </LevelTagColumn>
    <LabelColumn />
    <span style={{ flex: 1, color: Colors.RED3 }}>
      {`${node.error.message}\n${node.error.stack}`}
    </span>
  </>
);

const StepExpectationResultEvent: React.FunctionComponent<{
  node: LogsRowStructuredFragment_StepExpectationResultEvent;
}> = ({ node }) => (
  <>
    <LevelTagColumn>
      <Tag
        minimal={true}
        intent={node.expectationResult.success ? "success" : "danger"}
      >
        Expectation
      </Tag>
    </LevelTagColumn>
    <LabelColumn>{node.expectationResult.label}</LabelColumn>
    <MetadataEntries entries={node.expectationResult.metadataEntries} />
  </>
);

const StepMaterializationEvent: React.FunctionComponent<{
  node: LogsRowStructuredFragment_StepMaterializationEvent;
}> = ({ node }) => (
  <>
    <LevelTagColumn>
      <Tag minimal={true}>Materialization</Tag>
    </LevelTagColumn>
    <LabelColumn>{node.materialization.label}</LabelColumn>
    <MetadataEntries entries={node.materialization.metadataEntries} />
  </>
);

const ExecutionStepOutputEvent: React.FunctionComponent<{
  node: LogsRowStructuredFragment_ExecutionStepOutputEvent;
}> = ({ node }) => {
  const output =
    node.step && node.step.outputs.find(i => i.name === node.outputName);
  return (
    <>
      <LevelTagColumn>
        <Tag
          minimal={true}
          intent={node.typeCheck.success ? "success" : "warning"}
        >
          Output
        </Tag>
      </LevelTagColumn>
      <LabelColumn>
        {node.outputName}
        <br />
        {output && (
          <TypeName style={{ fontSize: 11 }}>
            {output.type.displayName}
          </TypeName>
        )}
      </LabelColumn>
      {node.typeCheck.metadataEntries.length ? (
        <MetadataEntries entries={node.typeCheck.metadataEntries} />
      ) : (
        <span style={{ flex: 1 }}>
          No typecheck metadata describing this output.
        </span>
      )}
    </>
  );
};

const ExecutionStepInputEvent: React.FunctionComponent<{
  node: LogsRowStructuredFragment_ExecutionStepInputEvent;
}> = ({ node }) => {
  const input =
    node.step && node.step.inputs.find(i => i.name === node.inputName);
  return (
    <>
      <LevelTagColumn>
        <Tag
          minimal={true}
          intent={node.typeCheck.success ? "success" : "warning"}
        >
          Input
        </Tag>
      </LevelTagColumn>
      <LabelColumn>
        {node.inputName}
        <br />
        {input && (
          <TypeName style={{ fontSize: 11 }}>{input.type.displayName}</TypeName>
        )}
      </LabelColumn>
      {node.typeCheck.metadataEntries.length ? (
        <MetadataEntries entries={node.typeCheck.metadataEntries} />
      ) : (
        <span style={{ flex: 1 }}>
          No typecheck metadata describing this output.
        </span>
      )}
    </>
  );
};
