import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {showCustomAlert} from '../CustomAlertProvider';

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

const OverflowBanner = styled.div`
  position: absolute;
  bottom: 0;
  right: 105px;
  user-select: none;
  font-size: 12px;
  background: ${Colors.LIGHT_GRAY3};
  border-top-left-radius: 4px;
  padding: 2px 12px;
  color: ${Colors.BLACK};
  &:hover {
    color: ${Colors.BLACK};
    background: ${Colors.LIGHT_GRAY1};
  }
`;

export class CellTruncationProvider extends React.Component<
  {
    style: React.CSSProperties;
    onExpand?: () => void;
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
        {this.state.isOverflowing && (
          <>
            <OverflowFade />
            <OverflowBanner onClick={this.onView}>View Full Message</OverflowBanner>
          </>
        )}
      </div>
    );
  }
}
