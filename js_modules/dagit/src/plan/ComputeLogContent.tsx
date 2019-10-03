import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import * as sc from "styled-components";
import { Spinner, Intent } from "@blueprintjs/core";
import Ansi from "ansi-to-react";
import { IStepState } from "../RunMetadataProvider";
import { ExecutionStateDot } from "./ExecutionStateDot";
import { ROOT_SERVER_URI } from "../Util";
import { ComputeLogContentFragment } from "./types/ComputeLogContentFragment";

interface IComputeLogContentProps {
  runState: IStepState;
  onRequestClose: () => void;
  computeLogs: ComputeLogContentFragment;
}

export class ComputeLogContent extends React.Component<
  IComputeLogContentProps
> {
  static fragments = {
    ComputeLogContentFragment: gql`
      fragment ComputeLogContentFileFragment on ComputeLogFile {
        path
        data
        downloadUrl
      }
      fragment ComputeLogContentFragment on ComputeLogs {
        stdout {
          ...ComputeLogContentFileFragment
        }
        stderr {
          ...ComputeLogContentFileFragment
        }
      }
    `
  };

  state = {
    selected: "stderr"
  };

  close = (e: React.SyntheticEvent) => {
    e.stopPropagation();
    this.props.onRequestClose();
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

  render() {
    const { computeLogs } = this.props;
    const { selected } = this.state;

    const logData = computeLogs[selected];
    if (!logData) {
      return null;
    }

    const { path, downloadUrl } = logData;
    const isRelativeUrl = (x?: string) => x && x.startsWith("/");
    const url = isRelativeUrl(downloadUrl)
      ? ROOT_SERVER_URI + downloadUrl
      : downloadUrl;

    return (
      <Container>
        <FileContainer>
          <FileHeader>
            <Row>
              <Tab
                selected={selected === "stderr"}
                onClick={() => this.setState({ selected: "stderr" })}
              >
                stderr
              </Tab>
              <Tab
                selected={selected === "stdout"}
                onClick={() => this.setState({ selected: "stdout" })}
              >
                stdout
              </Tab>
            </Row>
            <Row>
              {this.renderStatus()}
              <Link
                aria-label="Download link"
                className="bp3-button bp3-minimal bp3-icon-download"
                href={url}
                download
              >
                <LinkText>Download {selected}</LinkText>
              </Link>
              <button
                onClick={this.close}
                className="bp3-dialog-close-button bp3-button bp3-minimal bp3-icon-cross"
              ></button>
            </Row>
          </FileHeader>
          <FileContent
            content={(computeLogs.stdout && computeLogs.stdout.data) || ""}
            selected={selected === "stdout"}
          />
          <FileContent
            content={(computeLogs.stderr && computeLogs.stderr.data) || ""}
            selected={selected === "stderr"}
          />
          <FileFooter>{path}</FileFooter>
        </FileContainer>
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
  const { content } = props;
  if (!content) {
    return null;
  }
  const matches = content.match(/\n/g);
  const count = matches ? matches.length : 0;
  return (
    <LineNumberContainer>
      {Array.from(Array(count), (_, i) => (
        <div key={i}>{String(i + 1)}</div>
      ))}
    </LineNumberContainer>
  );
};

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
  margin-left: 10px;
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
  padding: 0 10px;
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
  ${({ selected }: { selected: boolean }) =>
    selected ? null : "visibility: hidden;"}
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
const Tab = styled.div`
  background-color: ${({ selected }: { selected: boolean }) =>
    selected ? "#333333" : "#444444"};
  cursor: pointer;
  height: 30px;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 0 150px;
  margin-right: 1px;
  margin-bottom: ${({ selected }: { selected: boolean }) =>
    selected ? "-10px" : "-9px"};
  border-top-right-radius: 5px;
  border-top-left-radius: 5px;
  border-top: 0.5px solid
    ${({ selected }: { selected: boolean }) =>
      selected ? "#5c7080" : "transparent"};
  border-left: 0.5px solid
    ${({ selected }: { selected: boolean }) =>
      selected ? "#5c7080" : "transparent"};
  border-right: 0.5px solid
    ${({ selected }: { selected: boolean }) =>
      selected ? "#5c7080" : "transparent"};
  &:hover {
    border-top: 0.5px solid #5c7080;
    border-left: 0.5px solid #5c7080;
    border-right: 0.5px solid #5c7080;
    height: ${({ selected }: { selected: boolean }) =>
      selected ? "30px" : "28px"};
  }
`;
