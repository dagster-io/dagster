import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import * as sc from "styled-components";
import { Dialog, Spinner, Intent } from "@blueprintjs/core";
import { RunContext } from "../runs/RunContext";
import { useQuery } from "react-apollo";
import Ansi from "ansi-to-react";
import { IStepState } from "../RunMetadataProvider";
import { ExecutionStateDot } from "./ExecutionStateDot";
import { ROOT_SERVER_URI } from "../Util";

export const COMPUTE_LOGS_QUERY = gql`
  query ComputeLogsQuery($runId: ID!, $stepKey: String!) {
    pipelineRunOrError(runId: $runId) {
      ... on PipelineRun {
        runId
        computeLogs(stepKey: $stepKey) {
          stdout {
            path
            data
            downloadUrl
          }
          stderr {
            path
            data
            downloadUrl
          }
          cursor
        }
      }
    }
  }
`;

const COMPUTE_LOGS_SUBSCRIPTION = gql`
  subscription ComputeLogsSubscription(
    $runId: ID!
    $stepKey: String!
    $cursor: Cursor
  ) {
    computeLogs(runId: $runId, stepKey: $stepKey, cursor: $cursor) {
      stdout {
        data
      }
      stderr {
        data
      }
      cursor
    }
  }
`;

interface ComputeLogModalProps {
  stepKey: string;
  isOpen: boolean;
  onRequestClose: () => void;
  runState: IStepState;
}

interface IComputeLogFile {
  path: string;
  data: string;
  downloadUrl: string;
}
interface IComputeLogFileUpdate {
  data: string;
}

export default ({
  isOpen,
  onRequestClose,
  stepKey,
  runState
}: ComputeLogModalProps) => {
  const run = React.useContext(RunContext);
  const runId = run ? run.runId : "";
  const { loading, data, error, subscribeToMore } = useQuery(
    COMPUTE_LOGS_QUERY,
    { variables: { runId, stepKey } }
  );
  const computeLogs =
    data && data.pipelineRunOrError && data.pipelineRunOrError.computeLogs;

  if (!run || !computeLogs) {
    return null;
  }

  const updateData = (prev: IComputeLogFile, update: IComputeLogFileUpdate) => {
    if (!prev && update) {
      return update;
    }
    if (prev && !update) {
      return prev;
    }
    return {
      ...prev,
      ...update,
      data: prev.data + update.data
    };
  };

  const subscribe = () => {
    return subscribeToMore({
      document: COMPUTE_LOGS_SUBSCRIPTION,
      variables: { runId, stepKey, cursor: computeLogs.cursor },
      updateQuery: (prev, { subscriptionData: { data } }) => {
        if (!data) return prev;
        return {
          ...prev,
          pipelineRunOrError: {
            ...prev.pipelineRunOrError,
            computeLogs: {
              ...prev.pipelineRunOrError.computeLogs,
              ...data.computeLogs,
              stdout: updateData(
                prev.pipelineRunOrError.computeLogs.stdout,
                data.computeLogs.stdout
              ),
              stderr: updateData(
                prev.pipelineRunOrError.computeLogs.stderr,
                data.computeLogs.stderr
              )
            }
          }
        };
      }
    });
  };

  return (
    <Dialog
      onClose={onRequestClose}
      style={{
        width: "100vw",
        height: "100vh",
        margin: 0,
        padding: 0,
        borderRadius: 0
      }}
      usePortal={true}
      isOpen={isOpen}
    >
      {loading && "Loading"}
      {error}
      {computeLogs && (
        <ComputeLogContent
          subscribe={subscribe}
          runState={runState}
          onRequestClose={onRequestClose}
          computeLogs={computeLogs}
        />
      )}
    </Dialog>
  );
};

interface IComputeLogContentProps {
  runState: IStepState;
  subscribe: () => void;
  onRequestClose: () => void;
  computeLogs: {
    stdout: IComputeLogFile;
    stderr: IComputeLogFile;
    cursor: string;
  };
}

export class ComputeLogContent extends React.Component<
  IComputeLogContentProps
> {
  state = {
    stdoutVisible: true,
    stderrVisible: true
  };

  componentDidMount() {
    this.props.subscribe();
  }

  close = (e: React.SyntheticEvent, type: string) => {
    e.stopPropagation();
    const { stderrVisible, stdoutVisible } = this.state;
    const keepModalOpen = type === "stdout" ? stderrVisible : stdoutVisible;
    if (keepModalOpen) {
      this.setState({
        stderrVisible: type !== "stderr",
        stdoutVisible: type !== "stdout"
      });
    } else {
      this.props.onRequestClose();
    }
  };

  renderStatus() {
    const { runState } = this.props;
    if (runState === IStepState.RUNNING) {
      return <Spinner intent={Intent.NONE} size={11} />;
    }
    return (
      <ExecutionStateDot
        state={runState}
        title={`${runState[0].toUpperCase()}${runState.substr(1)}`}
      />
    );
  }

  renderFile(type: string) {
    const { computeLogs } = this.props;
    const { stdoutVisible, stderrVisible } = this.state;
    const visible = type === "stdout" ? stdoutVisible : stderrVisible;
    if (!visible) {
      return null;
    }

    const content = computeLogs[type] ? computeLogs[type].data : "";
    const path = computeLogs[type] ? computeLogs[type].path : null;
    const isRelativeUrl = (x?: string) => x && x.startsWith("/");
    const downloadUrl = computeLogs[type]
      ? isRelativeUrl(computeLogs[type].downloadUrl)
        ? ROOT_SERVER_URI + computeLogs[type].downloadUrl
        : computeLogs[type].downloadUrl
      : null;

    return (
      <FileContainer>
        <FileHeader>
          <Row>
            {this.renderStatus()}
            <Title>{type}</Title>
          </Row>
          <Row>
            <Link
              aria-label="Download link"
              className="bp3-button bp3-minimal bp3-icon-download"
              href={downloadUrl}
              download
            >
              <LinkText>Download {type}</LinkText>
            </Link>
            <button
              onClick={e => this.close(e, type)}
              className="bp3-dialog-close-button bp3-button bp3-minimal bp3-icon-cross"
            ></button>
          </Row>
        </FileHeader>
        <FileContent content={content} />
        <FileFooter>{path}</FileFooter>
      </FileContainer>
    );
  }

  render() {
    return (
      <Container>
        {this.renderFile("stdout")}
        {this.renderFile("stderr")}
      </Container>
    );
  }
}

interface IScrollContainerProps {
  content: string;
  className?: string;
}

class ScrollContainer extends React.Component<IScrollContainerProps> {
  private container = React.createRef<HTMLDivElement>();

  componentDidMount() {
    this.scrollToBottom();
  }

  getSnapshotBeforeUpdate() {
    if (!this.container.current) {
      return false;
    }
    const { scrollHeight, scrollTop, offsetHeight } = this.container.current;
    const shouldScroll = offsetHeight + scrollTop >= scrollHeight;
    return shouldScroll;
  }

  componentDidUpdate(_props: any, _state: any, shouldScroll: boolean) {
    if (shouldScroll) {
      this.scrollToBottom();
    }
  }

  scrollToBottom() {
    const node = this.container.current;
    if (!node) {
      return;
    }

    node.scrollTop = node.scrollHeight - node.offsetHeight;
  }

  render() {
    const { content, className } = this.props;

    if (!content) {
      return (
        <div className={className} ref={this.container}>
          <ContentContainer
            style={{ justifyContent: "center", alignItems: "center" }}
          >
            No output
          </ContentContainer>
        </div>
      );
    }

    return (
      <div className={className} ref={this.container}>
        <ContentContainer>
          <LineNumbers content={content} />
          <Content>
            <SolarizedColors />
            <Ansi linkify={false} useClasses>
              {content}
            </Ansi>
          </Content>
        </ContentContainer>
      </div>
    );
  }
}

const LineNumbers = (props: IScrollContainerProps) => {
  const lines = props.content.split("\n");
  if (!lines || !lines.length) {
    return null;
  }
  const count = !lines[lines.length - 1]
    ? lines.slice(0, -1).length
    : lines.length;
  return (
    <LineNumberContainer>
      {Array.from(Array(count), (_, i) => (
        <div key={i}>{String(i + 1)}</div>
      ))}
    </LineNumberContainer>
  );
};

const Title = styled.div`
  margin-left: 10px;
`;
const Row = styled.div`
  display: flex;
  flex-direction: row;
  margin-left: 5px;
  align-items: center;
`;
const LinkText = styled.span`
  height: 1px;
  width: 1px;
  position: absolute;
  overflow: hidden;
  top: -10px;
`;
const Link = styled.a`
  ::before {
    margin: 0 !important;
  }
`;
const Container = styled.div`
  background-color: #333333;
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: row;
`;
const FileContainer = styled.div`
  flex: 1;
  height: 100%;
  position: relative;
  &:first-child {
    border-right: 0.5px solid #5c7080;
  }
`;
const FileHeader = styled.div`
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  height: 40px;
  background-color: #444444;
  border-bottom: 0.5px solid #5c7080;
  color: ${({ color }) => color || "#ffffff"};
  font-weight: 600;
  padding: 2px 10px;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
`;
const FileContent = styled(ScrollContainer)`
  position: absolute;
  top: 40px;
  bottom: 30px;
  left: 0;
  right: 0;
  color: #eeeeee;
  font-family: Consolas, Menlo, monospace;
  white-space: pre;
  overflow: auto;
`;
const FileFooter = styled.div`
  display: flex;
  flex-direction: row;
  align-items: center;
  height: 30px;
  border-top: 0.5px solid #5c7080;
  color: #aaaaaa;
  padding: 2px 5px;
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  font-size: 0.85em;
`;
const ContentContainer = styled.div`
  display: flex;
  flex-direction: row;
  min-height: 100%;
`;
const Content = styled.div`
  padding: 10px;
`;
const LineNumberContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  border-right: 1px solid #5c7080;
  padding: 10px 10px 10px 20px;
  margin-right: 5px;
  background-color: #333333;
  opacity: 0.8;
  color: #858585;
  min-height: 100%;
`;
const SolarizedColors = sc.createGlobalStyle`
  .ansi-black {
    color: #586e75;
  }
  .ansi-red {
    color: #dc322f;
  }
  .ansi-green {
    color: #859900;
  }
  .ansi-yellow {
    color: #b58900;
  }
  .ansi-blue {
    color: #268bd2;
  }
  .ansi-magenta {
    color: #d33682;
  }
  .ansi-cyan {
    color: #2aa198;
  }
  .ansi-white {
    color: #eee8d5;
  }
`;
