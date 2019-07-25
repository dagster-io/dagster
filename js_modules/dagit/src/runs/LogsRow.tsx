import * as React from "react";
import gql from "graphql-tag";
import { Tag, Colors } from "@blueprintjs/core";

import { LogLevel } from "../types/globalTypes";

import {
  LogsRowStructuredFragment,
  LogsRowStructuredFragment_ExecutionStepFailureEvent,
  LogsRowStructuredFragment_PipelineInitFailureEvent
} from "./types/LogsRowStructuredFragment";
import { LogsRowUnstructuredFragment } from "./types/LogsRowUnstructuredFragment";
import {
  Row,
  StructuredContent,
  EventTypeColumn,
  SolidColumn,
  TimestampColumn
} from "./LogsRowComponents";
import { MetadataEntries, MetadataEntry } from "./MetadataEntry";
import { assertUnreachable } from "../Util";
import { MetadataEntryFragment } from "./types/MetadataEntryFragment";

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
          message
        }
        ... on PipelineProcessStartEvent {
          message
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
        ... on ObjectStoreOperationEvent {
          step {
            key
          }
          operationResult {
            op
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
        return <FailureContent node={node} />;

      // Default Behavior
      case "PipelineProcessStartEvent":
        return <DefaultContent message={node.message} eventType="Starting" />;
      case "PipelineProcessStartedEvent":
        return <DefaultContent message={node.message} eventType="Started" />;
      case "ExecutionStepStartEvent":
        return <DefaultContent message={node.message} eventType="Step Start" />;
      case "ExecutionStepSkippedEvent":
        return <DefaultContent message={node.message} eventType="Skipped" />;
      case "ExecutionStepSuccessEvent":
        return (
          <DefaultContent message={node.message} eventType="Step Finished" />
        );
      case "ExecutionStepInputEvent":
        return (
          <DefaultContent
            message={node.message}
            eventType="Input"
            eventIntent={node.typeCheck.success ? "success" : "warning"}
            metadataEntries={node.typeCheck.metadataEntries}
          />
        );
      case "ExecutionStepOutputEvent":
        return (
          <DefaultContent
            message={node.message}
            eventType="Output"
            eventIntent={node.typeCheck.success ? "success" : "warning"}
            metadataEntries={node.typeCheck.metadataEntries}
          />
        );
      case "StepExpectationResultEvent":
        return (
          <DefaultContent
            message={node.message}
            eventType="Expectation"
            eventIntent={node.expectationResult.success ? "success" : "warning"}
            metadataEntries={node.expectationResult.metadataEntries}
          />
        );
      case "StepMaterializationEvent":
        return (
          <DefaultContent
            message={node.message}
            eventType="Materialization"
            metadataEntries={node.materialization.metadataEntries}
          />
        );
      case "ObjectStoreOperationEvent":
        return (
          <DefaultContent
            message={node.message}
            eventType={
              node.operationResult.op === "SET_OBJECT"
                ? "Store"
                : node.operationResult.op === "GET_OBJECT"
                ? "Retrieve"
                : ""
            }
            metadataEntries={node.operationResult.metadataEntries}
          />
        );
      case "PipelineFailureEvent":
      case "PipelineSuccessEvent":
      case "LogMessageEvent":
      case "PipelineStartEvent":
        return <DefaultContent message={node.message} />;

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
        <SolidColumn stepKey={"step" in node && node.step && node.step.key} />
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
        <SolidColumn stepKey={node.step && node.step.key} />
        <EventTypeColumn>{node.level}</EventTypeColumn>
        <span style={{ flex: 1 }}>{node.message}</span>
        <TimestampColumn time={node.timestamp} />
      </Row>
    );
  }
}

// Structured Content Renderers

const DefaultContent: React.FunctionComponent<{
  message: string;
  eventType?: string;
  eventIntent?: "success" | "danger" | "warning";
  metadataEntries?: MetadataEntryFragment[];
}> = ({ message, eventType, eventIntent, metadataEntries }) => {
  return (
    <>
      <EventTypeColumn>
        {eventType && (
          <Tag
            minimal={true}
            intent={eventIntent}
            style={{ fontSize: "0.9em" }}
          >
            {eventType}
          </Tag>
        )}
      </EventTypeColumn>
      <span style={{ flex: 1 }}>
        {message}
        {metadataEntries && metadataEntries.length > 0 && (
          <>
            <br />
            <MetadataEntries entries={metadataEntries} />
          </>
        )}
      </span>
    </>
  );
};

const FailureContent: React.FunctionComponent<{
  node:
    | LogsRowStructuredFragment_ExecutionStepFailureEvent
    | LogsRowStructuredFragment_PipelineInitFailureEvent;
}> = ({ node }) => (
  <>
    <EventTypeColumn>
      <Tag minimal={true} intent="danger" style={{ fontSize: "0.9em" }}>
        Failed
      </Tag>
    </EventTypeColumn>
    <span style={{ flex: 1, color: Colors.RED3 }}>
      {`${node.error.message}\n${node.error.stack}`}
    </span>
  </>
);
