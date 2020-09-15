import * as React from 'react';
import styled from 'styled-components/macro';
import ReactMarkdown from 'react-markdown';

interface IDescriptionProps {
  description: string | null;
}

interface IDescriptionState {
  hasMore: boolean;
  expanded: boolean;
}

const MaxHeight = 320;

/*
If `input` begins with whitespace and every line contains at least that whitespace,
it removes it. Otherwise, return the original string.
*/
function removeLeadingSpaces(input: string) {
  const leadingSpaces = /^\n?( +)/.exec(input);
  if (leadingSpaces == null) {
    return input;
  }

  const lines = input.split('\n');
  if (!lines.every((l) => l.substr(0, leadingSpaces[1].length).trim() === '')) {
    return input;
  }

  return lines.map((l) => l.substr(leadingSpaces[1].length)).join('\n');
}

export default class Description extends React.Component<IDescriptionProps, IDescriptionState> {
  private _container: React.RefObject<HTMLDivElement> = React.createRef();

  public state: IDescriptionState = {
    hasMore: false,
    expanded: false,
  };

  componentDidMount() {
    this.updateHandleState();
  }

  componentDidUpdate() {
    this.updateHandleState();
  }

  updateHandleState() {
    if (!this._container.current) {
      return;
    }
    const hasMore = this._container.current.clientHeight > MaxHeight;
    if (hasMore !== this.state.hasMore) {
      this.setState({hasMore});
    }
  }

  render() {
    if (!this.props.description || this.props.description.length === 0) {
      return null;
    }

    const {expanded, hasMore} = this.state;
    return (
      <Container
        onDoubleClick={() => {
          const sel = document.getSelection();
          if (!sel || !this._container.current) return;
          const range = document.createRange();
          range.selectNodeContents(this._container.current);
          sel.removeAllRanges();
          sel.addRange(range);
        }}
        style={{
          maxHeight: expanded ? undefined : MaxHeight,
        }}
      >
        {!expanded && hasMore && <Mask />}
        {hasMore && (
          <ShowMoreHandle onClick={() => this.setState({expanded: !expanded})}>
            {expanded ? 'Show Less' : 'Show More'}
          </ShowMoreHandle>
        )}

        <div ref={this._container} style={{overflowX: 'auto'}}>
          <ReactMarkdown source={removeLeadingSpaces(this.props.description)} />
        </div>
      </Container>
    );
  }
}

const Container = styled.div`
  overflow: hidden;
  font-size: 0.8rem;
  position: relative;
  p:last-child {
    margin-bottom: 5px;
  }
`;

const Mask = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    to bottom,
    rgba(255, 255, 255, 0) 0%,
    rgba(255, 255, 255, 0) 70%,
    rgba(255, 255, 255, 1)
  );
  pointer-events: none;
  border-bottom: 1px solid #eee;
`;

const ShowMoreHandle = styled.a`
  line-height: 20px;
  position: absolute;
  padding: 0 14px;
  bottom: 0;
  left: 50%;
  height: 20px;
  transform: translate(-50%);
  background: #eee;
`;
