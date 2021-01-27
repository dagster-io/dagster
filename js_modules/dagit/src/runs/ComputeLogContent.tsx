import {gql} from '@apollo/client';
import {Colors, Icon} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import Ansi from 'ansi-to-react';
import * as React from 'react';
import styled, {createGlobalStyle} from 'styled-components/macro';

import {ROOT_SERVER_URI} from 'src/app/DomUtils';
import {ExecutionStateDot} from 'src/runs/ExecutionStateDot';
import {IStepState} from 'src/runs/RunMetadataProvider';
import {ComputeLogContentFileFragment} from 'src/runs/types/ComputeLogContentFileFragment';
import {Spinner} from 'src/ui/Spinner';
import {FontFamily} from 'src/ui/styles';

interface IComputeLogContentProps {
  runState: IStepState;
  onRequestClose: () => void;
  stdout: ComputeLogContentFileFragment | null;
  stderr: ComputeLogContentFileFragment | null;
  maxBytes: number;
}

const TRUNCATE_PREFIX = '\u001b[33m...logs truncated...\u001b[39m\n';
const SCROLLER_LINK_TIMEOUT_MS = 3000;

export class ComputeLogContent extends React.Component<IComputeLogContentProps> {
  private timeout: number;
  private stdout = React.createRef<ScrollContainer>();
  private stderr = React.createRef<ScrollContainer>();

  state = {
    selected: 'stderr',
    showScrollToTop: false,
  };

  close = (e: React.SyntheticEvent) => {
    e.stopPropagation();
    this.props.onRequestClose();
  };

  onScrollUp = (position: number) => {
    this.cancelHide();

    if (!position) {
      this.hide();
    } else {
      this.setState({showScrollToTop: true});
      this.scheduleHide();
    }
  };

  onScrollDown = (_position: number) => {
    this.hide();
  };

  hide = () => {
    this.setState({showScrollToTop: false});
    if (this.timeout) {
      clearTimeout(this.timeout);
      this.timeout = 0;
    }
  };

  scheduleHide = () => {
    this.timeout = window.setTimeout(this.hide, SCROLLER_LINK_TIMEOUT_MS);
  };

  cancelHide = () => {
    if (this.timeout) {
      clearTimeout(this.timeout);
      this.timeout = 0;
    }
  };

  scrollToTop = () => {
    const {selected} = this.state;
    const ref = selected === 'stdout' ? this.stdout : this.stderr;
    ref.current && ref.current.scrollToTop();
  };

  getDownloadUrl() {
    const {stdout, stderr} = this.props;
    const {selected} = this.state;
    const logData = selected === 'stdout' ? stdout : stderr;
    const downloadUrl = logData?.downloadUrl;
    if (!downloadUrl) {
      return null;
    }
    const isRelativeUrl = (x?: string) => x && x.startsWith('/');
    return isRelativeUrl(downloadUrl) ? ROOT_SERVER_URI + downloadUrl : downloadUrl;
  }

  renderScrollToTop() {
    const {showScrollToTop} = this.state;

    if (!showScrollToTop) {
      return null;
    }

    return (
      <ScrollToast>
        <ScrollToTop
          onClick={() => this.scrollToTop()}
          onMouseOver={this.cancelHide}
          onMouseOut={this.scheduleHide}
        >
          <Icon icon={IconNames.ARROW_UP} style={{marginRight: 10}} />
          Scroll to top
        </ScrollToTop>
      </ScrollToast>
    );
  }

  renderStatus() {
    const {runState} = this.props;
    if (runState === IStepState.RUNNING) {
      return <Spinner purpose="body-text" />;
    }
    return (
      <ExecutionStateDot
        state={runState}
        title={`${runState[0].toUpperCase()}${runState.substr(1)}`}
      />
    );
  }

  renderContent(ioType: string, content: string | null | undefined) {
    const isTruncated = content && Buffer.byteLength(content, 'utf8') >= this.props.maxBytes;

    if (content && isTruncated) {
      const nextLine = content.indexOf('\n') + 1;
      const truncated = nextLine < content.length ? content.slice(nextLine) : content;
      content = TRUNCATE_PREFIX + truncated;
    }
    const downloadUrl = this.getDownloadUrl();
    const warning = isTruncated ? (
      <FileWarning>
        <Icon icon={IconNames.WARNING_SIGN} style={{marginRight: 10, color: Colors.ORANGE5}} />
        This log has exceeded the 5MB limit.{' '}
        {downloadUrl ? (
          <a href={downloadUrl} download>
            Download the full log file
          </a>
        ) : null}
        .
      </FileWarning>
    ) : null;

    const ref = ioType === 'stdout' ? this.stdout : this.stderr;
    const isSelected = this.state.selected === ioType;
    return (
      <FileContent isSelected={isSelected}>
        {warning}
        <RelativeContainer>
          <LogContent
            isSelected={isSelected}
            content={content}
            onScrollUp={this.onScrollUp}
            onScrollDown={this.onScrollDown}
            ref={ref}
          />
        </RelativeContainer>
      </FileContent>
    );
  }

  select = (selected: string) => {
    this.setState({selected});
    this.hide();
  };

  render() {
    const {stdout, stderr} = this.props;
    const {selected} = this.state;

    const logData = selected === 'stdout' ? stdout : stderr;
    const downloadUrl = this.getDownloadUrl();

    return (
      <Container>
        <FileContainer>
          <FileHeader>
            <Row>
              <Tab selected={selected === 'stderr'} onClick={() => this.select('stderr')}>
                stderr
              </Tab>
              <Tab selected={selected === 'stdout'} onClick={() => this.select('stdout')}>
                stdout
              </Tab>
            </Row>
            <Row>
              {this.renderStatus()}
              {downloadUrl ? (
                <Link
                  aria-label="Download link"
                  className="bp3-button bp3-minimal bp3-icon-download"
                  href={downloadUrl}
                  download
                >
                  <LinkText>Download {selected}</LinkText>
                </Link>
              ) : null}
              <button
                onClick={this.close}
                className="bp3-dialog-close-button bp3-button bp3-minimal bp3-icon-cross"
              ></button>
            </Row>
          </FileHeader>
          {this.renderScrollToTop()}
          {this.renderContent('stdout', stdout?.data)}
          {this.renderContent('stderr', stderr?.data)}
          <FileFooter>{logData?.path}</FileFooter>
        </FileContainer>
      </Container>
    );
  }
}

export const COMPUTE_LOG_CONTENT_FRAGMENT = gql`
  fragment ComputeLogContentFileFragment on ComputeLogFile {
    path
    cursor
    data
    downloadUrl
  }
`;

interface IScrollContainerProps {
  content: string | null | undefined;
  isSelected?: boolean;
  className?: string;
  onScrollUp?: (position: number) => void;
  onScrollDown?: (position: number) => void;
}

class ScrollContainer extends React.Component<IScrollContainerProps> {
  private container = React.createRef<HTMLDivElement>();
  private lastScroll = 0;

  componentDidMount() {
    this.scrollToBottom();
    if (this.container.current) {
      this.container.current.focus();
      this.container.current.addEventListener('scroll', this.onScroll);
    }
  }

  getSnapshotBeforeUpdate() {
    if (!this.container.current) {
      return false;
    }
    const {scrollHeight, scrollTop, offsetHeight} = this.container.current;
    const shouldScroll = offsetHeight + scrollTop >= scrollHeight;
    return shouldScroll;
  }

  componentDidUpdate(_props: any, _state: any, shouldScroll: boolean) {
    if (shouldScroll) {
      this.scrollToBottom();
    }
    if (this.props.isSelected && !_props.isSelected) {
      this.container.current && this.container.current.focus();
    }
  }

  onScroll = () => {
    if (!this.container.current || !this.props.isSelected) {
      return;
    }
    const {onScrollUp, onScrollDown} = this.props;

    const {scrollHeight, scrollTop, offsetHeight} = this.container.current;
    const position = scrollTop / (scrollHeight - offsetHeight);
    if (this.container.current.scrollTop < this.lastScroll) {
      onScrollUp && onScrollUp(position);
    } else {
      onScrollDown && onScrollDown(position);
    }
    this.lastScroll = this.container.current.scrollTop;
  };

  focus() {
    const node = this.container.current;
    if (!node) {
      return;
    }

    node.focus();
  }

  scrollToBottom() {
    const node = this.container.current;
    if (!node) {
      return;
    }

    node.scrollTop = node.scrollHeight - node.offsetHeight;
  }

  scrollToTop() {
    const node = this.container.current;
    if (!node) {
      return;
    }

    node.scrollTop = 0;
    node.focus();
  }

  render() {
    const {content, className} = this.props;
    if (!content) {
      return (
        <div className={className} ref={this.container}>
          <ContentContainer style={{justifyContent: 'center', alignItems: 'center'}}>
            {content == null ? 'No log file available' : 'No output'}
          </ContentContainer>
        </div>
      );
    }

    return (
      <div className={className} style={{outline: 'none'}} ref={this.container} tabIndex={0}>
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
  const {content} = props;
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
  color: ${({color}) => color || '#ffffff'};
  font-weight: 600;
  padding: 0 10px;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
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
const SolarizedColors = createGlobalStyle`
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
  background-color: ${({selected}: {selected: boolean}) => (selected ? '#333333' : '#444444')};
  cursor: pointer;
  height: 30px;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 0 150px;
  margin-right: 1px;
  margin-bottom: ${({selected}: {selected: boolean}) => (selected ? '-10px' : '-9px')};
  border-top-right-radius: 5px;
  border-top-left-radius: 5px;
  border-top: 0.5px solid
    ${({selected}: {selected: boolean}) => (selected ? '#5c7080' : 'transparent')};
  border-left: 0.5px solid
    ${({selected}: {selected: boolean}) => (selected ? '#5c7080' : 'transparent')};
  border-right: 0.5px solid
    ${({selected}: {selected: boolean}) => (selected ? '#5c7080' : 'transparent')};
  &:hover {
    border-top: 0.5px solid #5c7080;
    border-left: 0.5px solid #5c7080;
    border-right: 0.5px solid #5c7080;
    height: ${({selected}: {selected: boolean}) => (selected ? '30px' : '28px')};
  }
`;

const FileContent = styled.div`
  position: absolute;
  top: 40px;
  bottom: 30px;
  left: 0;
  right: 0;
  display: flex;
  flex-direction: column;
  ${({isSelected}: {isSelected: boolean}) => (isSelected ? null : 'visibility: hidden;')}
`;
const RelativeContainer = styled.div`
  flex: 1;
  position: relative;
`;
const LogContent = styled(ScrollContainer)`
  color: #eeeeee;
  font-family: ${FontFamily.monospace};
  white-space: pre;
  overflow: auto;
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
`;
const FileWarning = styled.div`
  background-color: #fffae3;
  padding: 10px 20px;
  margin: 20px 70px;
  border-radius: 5px;
`;
const ScrollToast = styled.div`
  position: absolute;
  top: 40px;
  height: 30px;
  left: 0;
  right: 0;
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: flex-start;
  z-index: 1;
`;
const ScrollToTop = styled.div`
  background-color: black;
  padding: 10px 20px;
  border-bottom-right-radius: 5px;
  border-bottom-left-radius: 5px;
  color: white;
  border-bottom: 0.5px solid #5c7080;
  border-left: 0.5px solid #5c7080;
  border-right: 0.5px solid #5c7080;
  cursor: pointer;
  &:hover {
    text-decoration: underline;
  }
`;
