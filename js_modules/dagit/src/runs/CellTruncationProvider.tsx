import * as React from "react";
import * as ReactDOM from "react-dom";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { showCustomAlert } from "../CustomAlertProvider";

const OverflowFade = styled.div`
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40px;
  user-select: none;
  pointer-events: none;
  background: linear-gradient(
    to bottom,
    rgba(245, 248, 250, 0) 0%,
    rgba(245, 248, 250, 255) 100%
  );
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
  { style: React.CSSProperties },
  { isOverflowing: boolean }
> {
  state = {
    isOverflowing: false
  };

  componentDidMount() {
    this.detectOverflow();
  }

  componentDidUpdate() {
    this.detectOverflow();
  }

  detectOverflow() {
    // eslint-disable-next-line react/no-find-dom-node
    const el = ReactDOM.findDOMNode(this);
    if (!el || !(el instanceof HTMLElement)) return;

    const child = el.firstElementChild;
    if (!child) return;

    const isOverflowing = child.scrollHeight > this.props.style.height!;
    if (isOverflowing !== this.state.isOverflowing) {
      this.setState({ isOverflowing });
    }
  }

  onView = () => {
    // eslint-disable-next-line react/no-find-dom-node
    const el = ReactDOM.findDOMNode(this) as HTMLElement;
    const message = el.firstChild && el.firstChild.textContent;
    if (!message) return;
    showCustomAlert({ message: message, pre: true });
  };

  render() {
    const { style } = this.props;

    return (
      <div style={style}>
        {this.props.children}
        {this.state.isOverflowing && (
          <>
            <OverflowFade />
            <OverflowBanner onClick={this.onView}>
              View Full Message
            </OverflowBanner>
          </>
        )}
      </div>
    );
  }
}
