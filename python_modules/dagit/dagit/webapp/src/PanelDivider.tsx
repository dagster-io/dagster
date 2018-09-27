import * as React from "react";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";

interface IDividerProps {
  onMove: (vw: number) => void;
}
interface IDividerState {
  down: boolean;
}

export class PanelDivider extends React.Component<
  IDividerProps,
  IDividerState
> {
  state = {
    down: false
  };

  onMouseDown = (event: React.MouseEvent<HTMLDivElement>) => {
    this.setState({ down: true });
    const onMouseMove = (event: MouseEvent) => {
      let vx = (event.clientX * 100) / window.innerWidth;
      this.props.onMove(vx);
    };
    const onMouseUp = (event: MouseEvent) => {
      this.setState({ down: false });
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };
    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
  };

  render() {
    return (
      <DividerWrapper down={this.state.down}>
        <DividerHitArea onMouseDown={this.onMouseDown} />
      </DividerWrapper>
    );
  }
}

const DividerWrapper = styled.div<{ down: boolean }>`
  width: 4px;
  background: ${Colors.WHITE};
  border-left: 1px solid ${p => (p.down ? Colors.GRAY5 : Colors.LIGHT_GRAY2)};
  border-right: 1px solid ${p => (p.down ? Colors.GRAY3 : Colors.GRAY5)};
  overflow: visible;
  position: relative;
`;

const DividerHitArea = styled.div`
  width: 17px;
  height: 100%;
  z-index: 2;
  cursor: ew-resize;
  position: relative;
  left: -8px;
`;
