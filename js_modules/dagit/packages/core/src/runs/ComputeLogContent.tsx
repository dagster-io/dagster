import {gql} from '@apollo/client';
import {Colors, Icon} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import Ansi from 'ansi-to-react';
import * as React from 'react';
import styled, {createGlobalStyle} from 'styled-components/macro';

import {Spinner} from '../ui/Spinner';
import {FontFamily} from '../ui/styles';

import {ComputeLogContentFileFragment} from './types/ComputeLogContentFileFragment';

const TRUNCATE_PREFIX = '\u001b[33m...logs truncated...\u001b[39m\n';
const SCROLLER_LINK_TIMEOUT_MS = 3000;
export const MAX_STREAMING_LOG_BYTES = 5242880; // 5 MB

export class ComputeLogContent extends React.Component<{
  logData?: ComputeLogContentFileFragment | null;
  downloadUrl?: string | null;
  isLoading?: boolean;
  isVisible: boolean;
}> {
  private timeout: number | null = null;
  private contentContainer = React.createRef<ScrollContainer>();

  state = {
    showScrollToTop: false,
  };

  hideWarning = () => {
    this.setState({showScrollToTop: false});
    if (this.timeout) {
      clearTimeout(this.timeout);
      this.timeout = 0;
    }
  };

  scheduleHideWarning = () => {
    this.timeout = window.setTimeout(this.hideWarning, SCROLLER_LINK_TIMEOUT_MS);
  };

  cancelHideWarning = () => {
    if (this.timeout) {
      clearTimeout(this.timeout);
      this.timeout = 0;
    }
  };

  onScrollUp = (position: number) => {
    this.cancelHideWarning();

    if (!position) {
      this.hideWarning();
    } else {
      this.setState({showScrollToTop: true});
      this.scheduleHideWarning();
    }
  };

  onScrollDown = (_position: number) => {
    this.hideWarning();
  };

  scrollToTop = () => {
    this.contentContainer.current && this.contentContainer.current.scrollToTop();
  };

  renderScrollToTop() {
    const {showScrollToTop} = this.state;

    if (!showScrollToTop) {
      return null;
    }

    return (
      <ScrollToast>
        <ScrollToTop
          onClick={() => this.scrollToTop()}
          onMouseOver={this.cancelHideWarning}
          onMouseOut={this.scheduleHideWarning}
        >
          <Icon icon={IconNames.ARROW_UP} style={{marginRight: 10}} />
          Scroll to top
        </ScrollToTop>
      </ScrollToast>
    );
  }

  render() {
    const {logData, isLoading, isVisible, downloadUrl} = this.props;
    let content = logData?.data;
    const isTruncated = content && Buffer.byteLength(content, 'utf8') >= MAX_STREAMING_LOG_BYTES;

    if (content && isTruncated) {
      const nextLine = content.indexOf('\n') + 1;
      const truncated = nextLine < content.length ? content.slice(nextLine) : content;
      content = TRUNCATE_PREFIX + truncated;
    }
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

    return (
      <>
        <FileContainer isVisible={isVisible}>
          {this.renderScrollToTop()}
          <FileContent>
            {warning}
            <RelativeContainer>
              <LogContent
                isSelected={true}
                content={content}
                onScrollUp={this.onScrollUp}
                onScrollDown={this.onScrollDown}
                ref={this.contentContainer}
              />
            </RelativeContainer>
          </FileContent>
          {isLoading ? (
            <LoadingContainer>
              <Spinner purpose="page" />
            </LoadingContainer>
          ) : null}
        </FileContainer>
        <FileFooter isVisible={isVisible}>{logData?.path}</FileFooter>
      </>
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

const FileContainer = styled.div`
  flex: 1;
  height: 100%;
  position: relative;
  &:first-child {
    border-right: 0.5px solid #5c7080;
  }
  display: flex;
  flex-direction: column;
  ${({isVisible}: {isVisible: boolean}) => (isVisible ? null : 'display: none;')}
`;
const FileFooter = styled.div`
  display: flex;
  flex-direction: row;
  align-items: center;
  height: 30px;
  background-color: ${Colors.DARK_GRAY2};
  border-top: 0.5px solid #5c7080;
  color: #aaaaaa;
  padding: 2px 5px;
  font-size: 0.85em;
  ${({isVisible}: {isVisible: boolean}) => (isVisible ? null : 'display: none;')}
`;
const ContentContainer = styled.div`
  display: flex;
  flex-direction: row;
  min-height: 100%;
  background-color: ${Colors.DARK_GRAY2};
`;
const Content = styled.div`
  padding: 10px;
  background-color: ${Colors.DARK_GRAY2};
`;
const LineNumberContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  border-right: 1px solid #5c7080;
  padding: 10px 10px 10px 20px;
  margin-right: 5px;
  background-color: ${Colors.DARK_GRAY2};
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
const FileContent = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
`;
const RelativeContainer = styled.div`
  flex: 1;
  position: relative;
`;
const LogContent = styled(ScrollContainer)`
  color: #eeeeee;
  font-family: ${FontFamily.monospace};
  font-size: 16px;
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
  height: 30px;
  top: 0;
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
const LoadingContainer = styled.div`
  display: flex;
  justifycontent: center;
  alignitems: center;
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
  backgroundcolor: ${Colors.DARK_GRAY3};
  opacity: 0.3;
`;
