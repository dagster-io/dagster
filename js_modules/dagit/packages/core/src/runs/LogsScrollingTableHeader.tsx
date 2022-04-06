import {Colors} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import {getJSONForKey} from '../hooks/useStateWithStorage';

const ColumnWidthsStorageKey = 'ColumnWidths';
const ColumnWidths = Object.assign(
  {
    eventType: 140,
    solid: 150,
    timestamp: 117,
  },
  getJSONForKey(ColumnWidthsStorageKey),
);

const MIN_COLUMN_WIDTH = 40;

export const ColumnWidthsContext = React.createContext({
  ...ColumnWidths,
  onChange: (_: typeof ColumnWidths) => {},
});

export class ColumnWidthsProvider extends React.Component<
  {onWidthsChanged: (widths: typeof ColumnWidths) => void},
  typeof ColumnWidths
> {
  state = ColumnWidths;

  onWidthsChangedFromContext = (columnWidths: typeof ColumnWidths) => {
    window.localStorage.setItem(ColumnWidthsStorageKey, JSON.stringify(columnWidths));
    this.props.onWidthsChanged(columnWidths);
    this.setState(columnWidths);
  };

  render() {
    return (
      <ColumnWidthsContext.Provider
        value={{
          ...this.state,
          onChange: this.onWidthsChangedFromContext,
        }}
      >
        {this.props.children}
      </ColumnWidthsContext.Provider>
    );
  }
}

interface HeaderProps extends React.HTMLProps<HTMLDivElement> {
  width: number;
  handleSide?: 'left' | 'right';
  onResize?: (width: number) => void;
}

interface HeaderState {
  isDragging: boolean;
  width: number;
  screenX: number;
}

class Header extends React.Component<HeaderProps, HeaderState> {
  state = {
    isDragging: false,
    width: 0,
    screenX: 0,
  };

  componentWillUnmount() {
    document.removeEventListener('mousemove', this.onMouseMove);
    document.removeEventListener('mouseup', this.onMouseUp);
  }

  onMouseDown = (m: React.MouseEvent<HTMLDivElement>) => {
    const {width} = this.props;
    this.setState({
      isDragging: true,
      screenX: m.screenX,
      width,
    });
    document.addEventListener('mousemove', this.onMouseMove);
    document.addEventListener('mouseup', this.onMouseUp);
  };

  onMouseMove = (evt: MouseEvent) => {
    const {onResize, handleSide} = this.props;
    const {isDragging, width, screenX} = this.state;
    if (!evt.screenX || !isDragging || !onResize) {
      return;
    }
    const dir = handleSide === 'left' ? -1 : 1;
    onResize(Math.max(MIN_COLUMN_WIDTH, width + (evt.screenX - screenX) * dir));
  };

  onMouseUp = () => {
    const {isDragging} = this.state;
    isDragging && this.setState({isDragging: false});
    document.removeEventListener('mousemove', this.onMouseMove);
    document.removeEventListener('mouseup', this.onMouseUp);
  };

  render() {
    const isDraggable = !!this.props.onResize;

    return (
      <HeaderContainer style={{width: this.props.width}}>
        <HeaderDragHandle
          onMouseDown={isDraggable ? this.onMouseDown : undefined}
          isDraggable={isDraggable}
          isDragging={this.state.isDragging}
          side={this.props.handleSide || 'right'}
        >
          <div />
        </HeaderDragHandle>
        <HeaderLabel>{this.props.children}</HeaderLabel>
      </HeaderContainer>
    );
  }
}

export const Headers = () => {
  const widths = React.useContext(ColumnWidthsContext);
  return (
    <HeadersContainer>
      <Header width={widths.solid} onResize={(width) => widths.onChange({...widths, solid: width})}>
        Op
      </Header>
      <Header
        width={widths.eventType}
        onResize={(width) => widths.onChange({...widths, eventType: width})}
      >
        Event Type
      </Header>
      <HeaderContainer style={{flex: 1}}>Info</HeaderContainer>
      <Header
        handleSide="left"
        width={widths.timestamp}
        onResize={(width) => widths.onChange({...widths, timestamp: width})}
      >
        Timestamp
      </Header>
    </HeadersContainer>
  );
};

const HeadersContainer = styled.div`
  display: flex;
  color: ${Colors.Gray400};
  text-transform: uppercase;
  font-size: 12px;
  border-bottom: 1px solid ${Colors.KeylineGray};
  z-index: 2;
`;

const HeaderContainer = styled.div`
  flex-shrink: 0;
  position: relative;
  user-select: none;
  display: inline-block;
  padding: 0 12px;
  line-height: 32px;
`;

// eslint-disable-next-line no-unexpected-multiline
const HeaderDragHandle = styled.div<{
  side: 'left' | 'right';
  isDraggable: boolean;
  isDragging: boolean;
}>`
  width: 1px;
  height: 20000px;
  position: absolute;
  cursor: ${({isDraggable}) => (isDraggable ? 'ew-resize' : 'default')};
  z-index: 2;
  ${({side}) => (side === 'right' ? `right: -2px;` : `left: -2px;`)}
  padding: 0 2px;
  & > div {
    width: 1px;
    height: 100%;
    background: ${({isDragging}) => (isDragging ? Colors.Gray400 : Colors.KeylineGray)};
  }
`;

const HeaderLabel = styled.div`
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
`;
