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

interface SplitPanelContainerProps {
  axis?: "horizontal" | "vertical";
  identifier: string;
  first: React.ReactNode;
  firstInitialPercent: number;
  firstMinSize?: number;
  second: React.ReactNode;
}
interface SplitPanelContainerState {
  size: number;
  key: string;
}

export class SplitPanelContainer extends React.Component<
  SplitPanelContainerProps,
  SplitPanelContainerState
> {
  constructor(props: SplitPanelContainerProps) {
    super(props);

    const key = `dagit.panel-width.${this.props.identifier}`;
    let size = Number(window.localStorage.getItem(key));
    if (size === 0 || isNaN(size)) {
      size = this.props.firstInitialPercent;
    }

    this.state = { size, key };
  }

  onChangeSize = (size: number) => {
    this.setState({ size });
    window.localStorage.setItem(this.state.key, `${size}`);
  };

  render() {
    const { firstMinSize, first, second } = this.props;
    const { size } = this.state;
    const axis = this.props.axis || "horizontal";

    return (
      <Container axis={axis} id="split-panel-container">
        <Split
          axis={axis}
          axisSize={size}
          style={{
            flexShrink: 0,
            [axis === "horizontal" ? "minWidth" : "minHeight"]: firstMinSize
          }}
        >
          {first}
        </Split>
        <PanelDivider axis={axis} onMove={this.onChangeSize} />
        <Split axis={axis}>{second}</Split>
      </Container>
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

  ref = React.createRef<any>();

  onMouseDown = () => {
    this.setState({ down: true });

    const onMouseMove = (event: MouseEvent) => {
      const parent = this.ref.current?.closest("#split-panel-container");
      if (!parent) return;
      const parentRect = parent.getBoundingClientRect();

      const vx =
        this.props.axis === "horizontal"
          ? ((event.clientX - parentRect.left) * 100) / window.innerWidth
          : ((event.clientY - parentRect.top) * 100) / window.innerHeight;

      this.props.onMove(Math.min(100, Math.max(0.001, vx)));
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
      <Wrapper down={this.state.down} ref={this.ref}>
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

const Split = styled.div<{
  axisSize?: number;
  axis: "vertical" | "horizontal";
}>`
  ${props =>
    props.axis === "horizontal"
      ? props.axisSize
        ? `width: ${props.axisSize}vw`
        : `flex: 1`
      : props.axisSize
      ? `height: ${props.axisSize}vh`
      : `flex: 1`};
  position: relative;
  flex-direction: column;
  display: flex;
  ${props => (props.axis === "horizontal" ? "min-width: 0" : "min-height: 0")};
`;

const Container = styled.div<{
  axis?: "horizontal" | "vertical";
}>`
  display: flex;
  flex-direction: ${({ axis }) => (axis === "vertical" ? "column" : "row")};
  flex: 1 1;
  width: 100%;
  min-${({ axis }) => (axis === "vertical" ? "height" : "width")}: 0;
`;
