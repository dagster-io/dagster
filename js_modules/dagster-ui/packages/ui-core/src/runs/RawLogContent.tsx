import {Colors, FontFamily, Group, Icon, Spinner} from '@dagster-io/ui-components';
import Ansi from 'ansi-to-react';
import * as React from 'react';
import {createGlobalStyle} from 'styled-components';
import clsx from 'clsx';
import styles from './RawLogContent.module.css';

const MAX_STREAMING_LOG_BYTES = 5242880; // 5 MB
const TRUNCATE_PREFIX = '\u001b[33m...logs truncated...\u001b[39m\n';
const SCROLLER_LINK_TIMEOUT_MS = 3000;

interface Props {
  logData: string | null;
  isLoading: boolean;
  isVisible: boolean;
  downloadUrl?: string | null;
  location?: string;
}

export const RawLogContent = React.memo((props: Props) => {
  const {logData, location, isLoading, isVisible, downloadUrl} = props;
  const contentContainer = React.useRef<ScrollContainer | null>(null);
  const timer = React.useRef<number>();
  const [showScrollToTop, setShowScrollToTop] = React.useState(false);
  const scrollToTop = () => {
    if (contentContainer.current) {
      contentContainer.current.scrollToTop();
    }
  };
  const cancelHideWarning = () => {
    if (timer.current) {
      clearTimeout(timer.current);
      timer.current = 0;
    }
  };
  const hideWarning = () => {
    setShowScrollToTop(false);
    cancelHideWarning();
  };
  const scheduleHideWarning = () => {
    timer.current = window.setTimeout(hideWarning, SCROLLER_LINK_TIMEOUT_MS);
  };
  const onScrollUp = (position: number) => {
    cancelHideWarning();

    if (!position) {
      hideWarning();
    } else {
      setShowScrollToTop(true);
      scheduleHideWarning();
    }
  };
  let content = logData;
  const isTruncated = shouldTruncate(content);

  if (content && isTruncated) {
    const nextLine = content.indexOf('\n') + 1;
    const truncated = nextLine < content.length ? content.slice(nextLine) : content;
    content = TRUNCATE_PREFIX + truncated;
  }
  const warning = isTruncated ? (
    <div className={styles.fileWarning}>
      <Group direction="row" spacing={8} alignItems="center">
        <Icon name="warning" color={Colors.accentYellow()} />
        <div>
          This log has exceeded the 5MB limit.{' '}
          {downloadUrl ? (
            <a href={downloadUrl} download>
              Download the full log file
            </a>
          ) : null}
        </div>
      </Group>
    </div>
  ) : null;

  return (
    <>
      <div className={clsx(styles.fileContainer, !isVisible && styles.fileContainerHidden)}>
        {showScrollToTop ? (
          <div className={styles.scrollToast}>
            <button
              className={styles.scrollToTop}
              onClick={scrollToTop}
              onMouseOver={cancelHideWarning}
              onMouseOut={scheduleHideWarning}
            >
              <Group direction="row" spacing={8} alignItems="center">
                <Icon name="arrow_upward" color={Colors.accentPrimary()} />
                Scroll to top
              </Group>
            </button>
          </div>
        ) : null}
        <div className={styles.fileContent}>
          {warning}
          <div className={styles.relativeContainer}>
            <ScrollContainer
              className={styles.logContent}
              isSelected={true}
              content={content}
              onScrollUp={onScrollUp}
              onScrollDown={hideWarning}
              ref={contentContainer}
            />
          </div>
        </div>
        {isLoading ? (
          <div className={styles.loadingContainer}>
            <Spinner purpose="page" />
          </div>
        ) : null}
      </div>
      {location ? (
        <div className={clsx(styles.fileFooter, !isVisible && styles.fileFooterHidden)}>
          {location}
        </div>
      ) : null}
    </>
  );
});

const shouldTruncate = (content: string | null | undefined) => {
  if (!content) {
    return false;
  }
  const encoder = new TextEncoder();
  return encoder.encode(content).length >= MAX_STREAMING_LOG_BYTES;
};

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

    // Note: The +1 here accounts for these numbers occasionally being off by 0.5px in FF
    const shouldScroll = offsetHeight + scrollTop + 1 >= scrollHeight;
    return shouldScroll;
  }

  componentDidUpdate(_props: any, _state: any, shouldScroll: boolean) {
    if (shouldScroll) {
      window.requestAnimationFrame(() => {
        this.scrollToBottom();
      });
    }
    if (this.props.isSelected && !_props.isSelected) {
      if (this.container.current) {
        this.container.current.focus();
      }
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
      if (onScrollUp) {
        onScrollUp(position);
      }
    } else {
      if (onScrollDown) {
        onScrollDown(position);
      }
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
          <div
            className={styles.contentContainer}
            style={{justifyContent: 'center', alignItems: 'center'}}
          >
            {content == null ? 'No log file available' : 'No output'}
          </div>
        </div>
      );
    }

    const onSelectAll = (e: React.KeyboardEvent) => {
      const range = document.createRange();
      const sel = document.getSelection();
      const contentEl = e.currentTarget.querySelector('[data-content]');
      if (!sel || !contentEl) {
        return;
      }
      range.selectNode(contentEl);
      sel.removeAllRanges();
      sel.addRange(range);
      e.preventDefault();
    };

    return (
      <div
        className={className}
        style={{outline: 'none'}}
        ref={this.container}
        tabIndex={0}
        onKeyDown={(e) => {
          if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
            onSelectAll(e);
          }
        }}
      >
        <div className={styles.contentContainer}>
          <LineNumbers content={content} />
          <div className={styles.content} data-content={true}>
            <SolarizedColors />
            <Ansi linkify={false} useClasses>
              {content}
            </Ansi>
          </div>
        </div>
      </div>
    );
  }
}

const LineNumbers = (props: IScrollContainerProps) => {
  const {content} = props;
  const lastCount = React.useRef(0);
  const container = React.createRef<HTMLDivElement>();

  const matches = (content || '').match(/\n/g);
  const count = matches ? matches.length : 0;

  // The common case here is 1+ new line numbers appearing on each render. Until we fully
  // virtualize this UI, a good solution is to append a new div containing just the added
  // line numbers. This avoids repaint + relayout of the existing line numbers, which takes
  // 100ms per 100k lines of logs.
  React.useLayoutEffect(() => {
    const containerEl = container.current;
    if (!containerEl) {
      return;
    }
    if (count < lastCount.current) {
      containerEl.textContent = '';
      lastCount.current = 0;
    }
    const div = document.createElement('div');
    const addedCount = count - lastCount.current;
    div.textContent = Array.from(Array(addedCount), (_, i) =>
      String(lastCount.current + i + 1),
    ).join('\n');
    containerEl.appendChild(div);
    lastCount.current = count;
  }, [container, count]);

  return <div className={styles.lineNumberContainer} ref={container} />;
};

const SolarizedColors = createGlobalStyle`
  .ansi-black {
    color: ${Colors.accentOlive()};
  }
  .ansi-red {
    color: ${Colors.accentRed()};
  }
  .ansi-green {
    color: ${Colors.accentGreen()};
  }
  .ansi-yellow {
    color: ${Colors.accentYellow()};
  }
  .ansi-blue {
    color: ${Colors.accentBlue()};
  }
  .ansi-magenta {
    color: ${Colors.textBlue()};
  }
  .ansi-cyan {
    color: ${Colors.accentCyan()};
  }
  .ansi-white {
    color: ${Colors.accentGray()};
  }
`;
