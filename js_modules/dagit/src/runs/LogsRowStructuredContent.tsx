import * as React from "react";
import { Tag, Colors } from "@blueprintjs/core";
import { LogsRowStructuredFragment } from "./types/LogsRowStructuredFragment";
import { EventTypeColumn } from "./LogsRowComponents";
import { MetadataEntries } from "./MetadataEntry";
import { assertUnreachable } from "../Util";
import { MetadataEntryFragment } from "./types/MetadataEntryFragment";
import { PythonErrorFragment } from "../types/PythonErrorFragment";

interface IStructuredContentProps {
  node: LogsRowStructuredFragment;
}

export const LogsRowStructuredContent: React.FunctionComponent<IStructuredContentProps> = ({
  node
}) => {
  switch (node.__typename) {
    // Errors
    case "PipelineInitFailureEvent":
      return (
        <FailureContent error={node.error} eventType="Pipeline Init Failed" />
      );
    case "ExecutionStepFailureEvent":
      return (
        <FailureContent
          eventType="Step Failed"
          error={node.error}
          metadataEntries={node?.failureMetadata?.metadataEntries}
        />
      );

    case "PipelineProcessStartEvent":
      return <DefaultContent message={node.message} eventType="Starting" />;
    case "PipelineProcessStartedEvent":
      return <DefaultContent message={node.message} eventType="Started" />;
    case "PipelineProcessExitedEvent":
      return <DefaultContent message={node.message} eventType="Exited" />;

    case "ExecutionStepStartEvent":
      return <DefaultContent message={node.message} eventType="Step Start" />;
    case "ExecutionStepSkippedEvent":
      return (
        <DefaultContent
          message={node.message}
          eventType="Step Skipped"
          eventIntent="warning"
        />
      );
    case "ExecutionStepSuccessEvent":
      return (
        <DefaultContent
          message={node.message}
          eventType="Step Finished"
          eventIntent="success"
        />
      );
    case "ExecutionStepInputEvent":
      return (
        <DefaultContent
          message={
            node.message +
            (node.typeCheck.description ? " " + node.typeCheck.description : "")
          }
          eventType="Input"
          eventIntent={node.typeCheck.success ? "success" : "warning"}
        >
          <MetadataEntries entries={node.typeCheck.metadataEntries} />
        </DefaultContent>
      );
    case "ExecutionStepOutputEvent":
      return (
        <DefaultContent
          message={
            node.message +
            (node.typeCheck.description ? " " + node.typeCheck.description : "")
          }
          eventType="Output"
          eventIntent={node.typeCheck.success ? "success" : "warning"}
        >
          <MetadataEntries entries={node.typeCheck.metadataEntries} />
        </DefaultContent>
      );
    case "StepExpectationResultEvent":
      return (
        <DefaultContent
          message={node.message}
          eventType="Expectation"
          eventIntent={node.expectationResult.success ? "success" : "warning"}
        >
          <MetadataEntries entries={node.expectationResult.metadataEntries} />
        </DefaultContent>
      );
    case "StepMaterializationEvent":
      return (
        <DefaultContent message={node.message} eventType="Materialization">
          <MetadataEntries entries={node.materialization.metadataEntries} />
        </DefaultContent>
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
        >
          <MetadataEntries entries={node.operationResult.metadataEntries} />
        </DefaultContent>
      );
    case "PipelineFailureEvent":
      return (
        <DefaultContent
          message={node.message}
          eventType="Pipeline Failed"
          eventIntent="danger"
        />
      );
    case "PipelineSuccessEvent":
      return (
        <DefaultContent
          message={node.message}
          eventType="Pipeline Finished"
          eventIntent="success"
        />
      );

    case "PipelineStartEvent":
      return (
        <DefaultContent message={node.message} eventType="Pipeline Started" />
      );
    case "EngineEvent":
      if (node.engineError) {
        return (
          <FailureContent error={node.engineError} eventType="Engine Event" />
        );
      }
      return (
        <DefaultContent message={node.message} eventType="Engine Event">
          <MetadataEntries entries={node.metadataEntries} />
        </DefaultContent>
      );
    case "LogMessageEvent":
      return <DefaultContent message={node.message} />;
    default:
      // This allows us to check that the switch is exhaustive because the union type should
      // have been narrowed following each successive case to `never` at this point.
      return assertUnreachable(node);
  }
};

// Structured Content Renderers

const DefaultContent: React.FunctionComponent<{
  message: string;
  eventType?: string;
  eventIntent?: "success" | "danger" | "warning";
  metadataEntries?: MetadataEntryFragment[];
  children?: React.ReactElement;
}> = ({ message, eventType, eventIntent, children }) => {
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
        {children}
      </span>
    </>
  );
};

const FailureContent: React.FunctionComponent<{
  eventType: string;
  error: PythonErrorFragment;
  metadataEntries?: MetadataEntryFragment[];
}> = ({ error, eventType, metadataEntries }) => (
  <>
    <EventTypeColumn>
      <Tag minimal={true} intent="danger" style={{ fontSize: "0.9em" }}>
        {eventType}
      </Tag>
    </EventTypeColumn>
    <span style={{ flex: 1 }}>
      <span style={{ color: Colors.RED3 }}>{`${error.message}`}</span>
      <MetadataEntries entries={metadataEntries} />
      <span style={{ color: Colors.RED3 }}>
        {`\nStack Trace:\n${error.stack}`}
      </span>
    </span>
  </>
);
