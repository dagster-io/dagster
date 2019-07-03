import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { LogLevel } from "src/types/globalTypes";
import { IconNames } from "@blueprintjs/icons";
import { Tag, Colors, Icon } from "@blueprintjs/core";

import { HighlightedCodeBlock } from "../HighlightedCodeBlock";
import {
  LogsRowStructuredFragment,
  LogsRowStructuredFragment_ExecutionStepFailureEvent,
  LogsRowStructuredFragment_StepMaterializationEvent,
  LogsRowStructuredFragment_ExecutionStepOutputEvent,
  LogsRowStructuredFragment_ExecutionStepInputEvent,
  LogsRowStructuredFragment_StepExpectationResultEvent,
  LogsRowStructuredFragment_PipelineProcessStartedEvent,
  LogsRowStructuredFragment_PipelineInitFailureEvent,
  LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries
} from "./types/LogsRowStructuredFragment";
import { LogsRowUnstructuredFragment } from "./types/LogsRowUnstructuredFragment";
import { Cell, StructuredContent } from "./Cells";
import { copyValue } from "../Util";
import { showCustomAlert } from "../CustomAlertProvider";

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
        return (
          <DefaultStructuredEmptyEvent
            node={node}
            message={node.message}
            level={<Tag minimal={true}>Step Start</Tag>}
          />
        );
      case "ExecutionStepSkippedEvent":
        return (
          <DefaultStructuredEmptyEvent
            node={node}
            message={node.message}
            level={<Tag minimal={true}>Skipped</Tag>}
          />
        );
      case "ExecutionStepSuccessEvent":
        return (
          <DefaultStructuredEmptyEvent
            node={node}
            message={node.message}
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
      <Cell level={LogLevel.INFO}>
        <StepKeyColumn stepKey={"step" in node && node.step && node.step.key} />
        <StructuredContent>{this.renderStructuredContent()}</StructuredContent>
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
  width: 140px;
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
    <LevelContainer>
      <Tag minimal={true}>Started</Tag>
    </LevelContainer>
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
    <LevelContainer>
      <Tag minimal={true} intent="danger">
        Failed
      </Tag>
    </LevelContainer>
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
    <LevelContainer>
      <Tag
        minimal={true}
        intent={node.expectationResult.success ? "success" : "danger"}
      >
        Expectation
      </Tag>
    </LevelContainer>
    <span style={{ flex: 1 }}>
      <DisplayEventHeader>«{node.expectationResult.label}»</DisplayEventHeader>
      {node.expectationResult.metadataEntries.map((item, idx) => (
        <MetadataEntry entry={item} key={idx} />
      ))}
    </span>
  </>
);

const StepMaterializationEvent = ({
  node
}: {
  node: LogsRowStructuredFragment_StepMaterializationEvent;
}) => (
  <>
    <LevelContainer>
      <Tag minimal={true}>Materialization</Tag>
    </LevelContainer>
    <span style={{ flex: 1 }}>
      <DisplayEventHeader>«{node.materialization.label}»</DisplayEventHeader>
      {node.materialization.metadataEntries.map((item, idx) => (
        <MetadataEntry entry={item} key={idx} />
      ))}
    </span>
  </>
);

const DefaultStructuredEmptyEvent = ({
  node,
  message,
  level
}: {
  message: string;
  node: LogsRowStructuredFragment;
  level?: React.ReactNode;
}) => (
  <>
    <LevelContainer>{level}</LevelContainer>
    <span style={{ flex: 1 }}>{message}</span>
  </>
);

const ExecutionStepFailureEvent = ({
  node
}: {
  node: LogsRowStructuredFragment_ExecutionStepFailureEvent;
}) => (
  <>
    <LevelContainer>
      <Tag minimal={true} intent="danger">
        Failure
      </Tag>
    </LevelContainer>
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

const DisplayEventContainer = styled.div`
  white-space: pre-wrap;
  font-size: 12px;
`;

const DisplayEventHeader = styled.div`
  display: flex;
  align-items: baseline;
  font-weight: 600;
`;

const DisplayEventItemContainer = styled.div`
  display: block;
  padding-left: 15px;
`;

const DisplayEventLink = styled.a`
  text-decoration: underline;
  color: inherit;
  &:hover {
    color: inherit;
  }
`;

const MetadataEntry: React.FunctionComponent<{
  entry: LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries;
}> = ({ entry }) => {
  switch (entry.__typename) {
    case "EventPathMetadataEntry":
      return (
        <DisplayEventItemContainer>
          {entry.label}:
          <DisplayEventLink
            title={"Copy to clipboard"}
            onClick={e => copyValue(e, entry.path)}
          >
            [Copy Path]
          </DisplayEventLink>
        </DisplayEventItemContainer>
      );

    case "EventJsonMetadataEntry":
      return (
        <DisplayEventItemContainer>
          {entry.label}:
          <DisplayEventLink
            title="Show full value"
            onClick={() =>
              showCustomAlert({
                message: JSON.stringify(JSON.parse(entry.jsonString), null, 2),
                pre: true,
                title: "Value"
              })
            }
          >
            [Show Metadata]
          </DisplayEventLink>
        </DisplayEventItemContainer>
      );

    case "EventUrlMetadataEntry":
      return (
        <DisplayEventItemContainer>
          {entry.label}:
          <DisplayEventLink
            href={entry.url}
            title={`Open in a new tab`}
            target="__blank"
          >
            [Open URL]
          </DisplayEventLink>
        </DisplayEventItemContainer>
      );
    case "EventTextMetadataEntry":
      return (
        <DisplayEventItemContainer>
          {entry.label}: {entry.text}
        </DisplayEventItemContainer>
      );
    default:
      return assertUnreachable(entry);
  }
};
