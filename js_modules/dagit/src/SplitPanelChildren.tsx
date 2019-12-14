import * as React from "react";
import styled from "styled-components/macro";
import { Colors } from "@blueprintjs/core";

interface IDividerProps {
  axis: "horizontal" | "vertical";
  onMove: (vw: number) => void;
}
interface IDividerState {
  down: boolean;
}

interface SplitPanelChildrenProps {
  identifier: string;
  left: React.ReactNode;
  leftInitialPercent: number;
  leftMinWidth?: number;
  right: React.ReactNode;
}
interface SplitPanelChildrenState {
  width: number;
  key: string;
}

export class SplitPanelChildren extends React.Component<
  SplitPanelChildrenProps,
  SplitPanelChildrenState
> {
  constructor(props: SplitPanelChildrenProps) {
    super(props);

    const key = `dagit.panel-width.${this.props.identifier}`;
    let width = Number(window.localStorage.getItem(key));
    if (width === 0 || isNaN(width)) {
      width = this.props.leftInitialPercent;
    }

    this.state = { width, key };
  }

  onChangeWidth = (vw: number) => {
    this.setState({ width: vw });
    window.localStorage.setItem(this.state.key, `${vw}`);
  };

  render() {
    const { leftMinWidth, left, right } = this.props;
    const { width } = this.state;

    return (
      <>
        <Split width={width} style={{ flexShrink: 0, minWidth: leftMinWidth }}>
          {left}
        </Split>
        <PanelDivider axis="horizontal" onMove={this.onChangeWidth} />
        <Split>{right}</Split>
      </>
    );
  }
}

export class PanelDivider extends React.Component<
  IDividerProps,
  IDividerState
> {
  state = {
    down: false
  };

  onMouseDown = () => {
    this.setState({ down: true });
    const onMouseMove = (event: MouseEvent) => {
      this.props.onMove(
        this.props.axis === "horizontal"
          ? (event.clientX * 100) / window.innerWidth
          : (event.clientY * 100) / window.innerHeight
      );
    };
    const onMouseUp = () => {
      this.setState({ down: false });
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };
    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
  };

  render() {
    const Wrapper = DividerWrapper[this.props.axis];
    const HitArea = DividerHitArea[this.props.axis];
    return (
      <Wrapper down={this.state.down}>
        <HitArea onMouseDown={this.onMouseDown} />
      </Wrapper>
    );
  }
}

const DividerWrapper = {
  horizontal: styled.div<{ down: boolean }>`
    width: 4px;
    background: ${Colors.WHITE};
    border-left: 1px solid ${p => (p.down ? Colors.GRAY5 : Colors.LIGHT_GRAY2)};
    border-right: 1px solid ${p => (p.down ? Colors.GRAY3 : Colors.GRAY5)};
    overflow: visible;
    position: relative;
  `,
  vertical: styled.div<{ down: boolean }>`
    height: 4px;
    background: ${Colors.WHITE};
    border-top: 1px solid ${p => (p.down ? Colors.GRAY5 : Colors.LIGHT_GRAY2)};
    border-bottom: 1px solid ${p => (p.down ? Colors.GRAY3 : Colors.GRAY5)};
    overflow: visible;
    position: relative;
  `
};

const DividerHitArea = {
  horizontal: styled.div`
    width: 17px;
    height: 100%;
    z-index: 2;
    cursor: ew-resize;
    position: relative;
    left: -8px;
  `,
  vertical: styled.div`
    height: 17px;
    width: 100%;
    z-index: 2;
    cursor: ns-resize;
    position: relative;
    top: -8px;
  `
};

const Split = styled.div<{ width?: number }>`
  ${props => (props.width ? `width: ${props.width}vw` : `flex: 1`)};
  position: relative;
  flex-direction: column;
  display: flex;
  min-width: 0;
`;
