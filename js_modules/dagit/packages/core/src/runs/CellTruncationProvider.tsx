import {Colors} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import {showCustomAlert} from '../app/CustomAlertProvider';

const OverflowFade = styled.div`
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40px;
  user-select: none;
  pointer-events: none;
  background: linear-gradient(to bottom, rgba(245, 248, 250, 0) 0%, rgba(245, 248, 250, 255) 100%);
`;

const OverflowButtonContainer = styled.div`
  position: absolute;
  bottom: 6px;
  left: 0;
  right: 0;
  display: flex;
  flex-direction: row;
  justify-content: center;
`;

const OverflowButton = styled.button`
  border: 0;
  cursor: pointer;
  user-select: none;
  font-size: 12px;
  font-weight: 500;
  background: rgba(100, 100, 100, 0.7);
  border-radius: 4px;
  line-height: 32px;
  padding: 0 12px;
  color: ${Colors.White};
  &:hover {
    background: rgba(100, 100, 100, 0.85);
  }

  &:focus,
  &:active {
    outline: none;
  }

  &:active {
    background: rgba(0, 0, 0, 0.7);
  }
`;

export class CellTruncationProvider extends React.Component<
  {
    style: React.CSSProperties;
    onExpand?: () => void;
    forceExpandability?: boolean;
  },
  {isOverflowing: boolean}
> {
  state = {
    isOverflowing: false,
  };

  private contentContainerRef: React.RefObject<HTMLDivElement> = React.createRef();

  componentDidMount() {
    this.detectOverflow();
  }

  componentDidUpdate() {
    this.detectOverflow();
  }

  detectOverflow() {
    const child =
      this.contentContainerRef.current && this.contentContainerRef.current.firstElementChild;

    if (!child) {
      return;
    }

    const isOverflowing = child.scrollHeight > this.props.style.height!;
    if (isOverflowing !== this.state.isOverflowing) {
      this.setState({isOverflowing});
    }
  }

  defaultExpand() {
    const message =
      this.contentContainerRef.current && this.contentContainerRef.current.textContent;
    message &&
      showCustomAlert({
        body: <div style={{whiteSpace: 'pre-wrap'}}>{message}</div>,
      });
  }

  onView = () => {
    const {onExpand} = this.props;
    onExpand ? onExpand() : this.defaultExpand();
  };

  render() {
    const style = {...this.props.style, overflow: 'hidden'};

    return (
      <div style={style}>
        <div ref={this.contentContainerRef}>{this.props.children}</div>
        {(this.state.isOverflowing || this.props.forceExpandability) && (
          <>
            <OverflowFade />
            <OverflowButtonContainer>
              <OverflowButton onClick={this.onView}>View full message</OverflowButton>
            </OverflowButtonContainer>
          </>
        )}
      </div>
    );
  }
}
