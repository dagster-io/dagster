import * as React from "react";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";

const ColumnWidthsStorageKey = "ColumnWidths";
const ColumnWidths = {
  eventType: 140,
  solid: 150,
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
  onChange: (_: typeof ColumnWidths) => {}
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

interface HeaderProps extends React.HTMLProps<HTMLDivElement> {
  width: number;
  handleSide?: "left" | "right";
  onResize?: (width: number) => void;
}

interface HeaderState {
  dragging: boolean;
}

class Header extends React.Component<HeaderProps, HeaderState> {
  state = {
    dragging: false
  };

  onMouseDown = (m: React.MouseEvent<HTMLDivElement>) => {
    const initialX = m.screenX;
    const initialWidth = this.props.width;

    const onMouseMove = (evt: Event) => {
      const dir = this.props.handleSide === "left" ? -1 : 1;
      const m = (evt as unknown) as React.MouseEvent<HTMLDivElement>;
      const screenX = m.screenX;

      this.props.onResize &&
        this.props.onResize(
          Math.max(40, initialWidth + (screenX - initialX) * dir)
        );
    };
    const onMouseUp = () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
      this.setState({ dragging: false });
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
    this.setState({ dragging: true });
  };

  render() {
    const draggable = !!this.props.onResize;

    return (
      <HeaderContainer style={{ width: this.props.width }}>
        <HeaderDragHandle
          onMouseDown={draggable ? this.onMouseDown : undefined}
          draggable={draggable}
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

export const Headers: React.FunctionComponent<{}> = () => {
  const widths = React.useContext(ColumnWidthsContext);
  return (
    <HeadersContainer>
      <Header
        width={widths.solid}
        onResize={width => widths.onChange({ ...widths, solid: width })}
      >
        Solid
      </Header>
      <Header
        width={widths.eventType}
        onResize={width => widths.onChange({ ...widths, eventType: width })}
      >
        Event Type
      </Header>
      <HeaderContainer style={{ flex: 1 }}>Info</HeaderContainer>
      <Header handleSide="left" width={widths.timestamp}>
        Timestamp
      </Header>
    </HeadersContainer>
  );
};

const HeadersContainer = styled.div`
  display: flex;
  color: ${Colors.GRAY3};
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

// eslint-disable-next-line no-unexpected-multiline
const HeaderDragHandle = styled.div<{
  side: "left" | "right";
  draggable: boolean;
  dragging: boolean;
}>`
  width: 17px;
  height: 20000px;
  position: absolute;
  cursor: ${({ draggable }) => (draggable ? "ew-resize" : "default")};
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
