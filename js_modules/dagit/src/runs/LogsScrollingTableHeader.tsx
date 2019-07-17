import * as React from "react";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";

const ColumnWidthsStorageKey = "ColumnWidths";
const ColumnWidths = {
  label: 160,
  levelTag: 140,
  stepKey: 150,
  timestamp: 100
};

try {
  const saved = window.localStorage.getItem(ColumnWidthsStorageKey);
  Object.assign(ColumnWidths, JSON.parse(saved || "{}"));
} catch (err) {
  // no-op
}

export const ColumnWidthsContext = React.createContext({
  ...ColumnWidths,
  onChange: (vals: typeof ColumnWidths) => {}
});

export class ColumnWidthsProvider extends React.Component<
  { onWidthsChanged: (widths: typeof ColumnWidths) => void },
  typeof ColumnWidths
> {
  state = ColumnWidths;

  onWidthsChangedFromContext = (columnWidths: typeof ColumnWidths) => {
    window.localStorage.setItem(
      ColumnWidthsStorageKey,
      JSON.stringify(columnWidths)
    );
    this.props.onWidthsChanged(columnWidths);
    this.setState(columnWidths);
  };

  render() {
    return (
      <ColumnWidthsContext.Provider
        value={{
          ...this.state,
          onChange: this.onWidthsChangedFromContext
        }}
      >
        {this.props.children}
      </ColumnWidthsContext.Provider>
    );
  }
}

interface ResizableHeaderProps extends React.HTMLProps<HTMLDivElement> {
  width: number;
  handleSide?: "left" | "right";
  onResize: (width: number) => void;
}

interface ResizableHeaderState {
  dragging: boolean;
}

class ResizableHeader extends React.Component<
  ResizableHeaderProps,
  ResizableHeaderState
> {
  state = {
    dragging: false
  };

  onMouseDown = (m: React.MouseEvent<HTMLDivElement>) => {
    const initialX = m.screenX;
    const initialWidth = this.props.width;

    const onMouseMove = (m: MouseEvent) => {
      const dir = this.props.handleSide === "left" ? -1 : 1;
      this.props.onResize(
        Math.max(40, initialWidth + (m.screenX - initialX) * dir)
      );
    };
    const onMouseUp = (m: MouseEvent) => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
      this.setState({ dragging: false });
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
    this.setState({ dragging: true });
  };

  render() {
    return (
      <HeaderContainer
        style={{
          width: this.props.width,
          textAlign: this.props.handleSide === "left" ? "right" : "left"
        }}
      >
        <HeaderDragHandle
          onMouseDown={this.onMouseDown}
          dragging={this.state.dragging}
          side={this.props.handleSide || "right"}
        >
          <div />
        </HeaderDragHandle>
        {this.props.children}
      </HeaderContainer>
    );
  }
}

export const Headers: React.FunctionComponent<{}> = props => {
  const widths = React.useContext(ColumnWidthsContext);
  return (
    <HeadersContainer>
      <ResizableHeader
        width={widths.stepKey}
        onResize={width => widths.onChange({ ...widths, stepKey: width })}
      >
        Solid
      </ResizableHeader>
      <ResizableHeader
        width={widths.levelTag}
        onResize={width => widths.onChange({ ...widths, levelTag: width })}
      >
        Event Type
      </ResizableHeader>
      <ResizableHeader
        width={widths.label}
        onResize={width => widths.onChange({ ...widths, label: width })}
      >
        Label
      </ResizableHeader>
      <HeaderContainer style={{ flex: 1 }}>Info</HeaderContainer>
      <HeaderContainer style={{ width: widths.timestamp }} />
    </HeadersContainer>
  );
};

const HeadersContainer = styled.div`
  display: flex;
  color: gray;
  text-transform: uppercase;
  font-size: 11px;
  border-bottom: 1px solid #cbd4da;
`;

const HeaderContainer = styled.div`
  flex-shrink: 0;
  position: relative;
  user-select: none;
  display: inline-block;
  padding: 4px 8px;
`;

const HeaderDragHandle = styled.div<{
  side: "left" | "right";
  dragging: boolean;
}>`
  width: 17px;
  height: 20000px;
  position: absolute;
  cursor: ew-resize;
  z-index: 2;
  ${({ side }) => (side === "right" ? `right: -13px;` : `left: -13px;`)}
  padding: 0 8px;
  & > div {
    width: 1px;
    height: 100%;
    background: ${({ dragging }) =>
      dragging ? Colors.GRAY1 : Colors.LIGHT_GRAY3};
  }
`;
