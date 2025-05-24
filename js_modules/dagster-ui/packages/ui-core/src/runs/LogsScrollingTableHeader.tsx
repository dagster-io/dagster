import {Colors} from '@dagster-io/ui-components';
import * as React from 'react';

import {getJSONForKey} from '../hooks/useStateWithStorage';
import styles from './LogsScrollingTableHeader.module.css';

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
  {children: React.ReactNode; onWidthsChanged?: (widths: typeof ColumnWidths) => void},
  typeof ColumnWidths
> {
  state = ColumnWidths;

  onWidthsChangedFromContext = (columnWidths: typeof ColumnWidths) => {
    window.localStorage.setItem(ColumnWidthsStorageKey, JSON.stringify(columnWidths));
    if (this.props.onWidthsChanged) {
      this.props.onWidthsChanged(columnWidths);
    }
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

interface HeaderProps extends Omit<React.HTMLProps<HTMLDivElement>, 'onResize'> {
  width: number;
  handleSide?: 'left' | 'right';
  onResize?: (width: number) => void;
}

interface HeaderState {
  isDragging: boolean;
  width: number;
  screenX: number;
}

export class Header extends React.Component<HeaderProps, HeaderState> {
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
    if (isDragging) {
      this.setState({isDragging: false});
    }
    document.removeEventListener('mousemove', this.onMouseMove);
    document.removeEventListener('mouseup', this.onMouseUp);
  };

  render() {
    const isDraggable = !!this.props.onResize;

    return (
      <div className={styles.headerContainer} style={{width: this.props.width}}>
        <div
          className={styles.headerDragHandle}
          onMouseDown={isDraggable ? this.onMouseDown : undefined}
          style={{
            cursor: isDraggable ? 'ew-resize' : 'default',
            zIndex: 2,
            right: this.props.handleSide === 'right' ? '-2px' : undefined,
            left: this.props.handleSide === 'left' ? '-2px' : undefined,
          }}
        >
          <div
            style={{
              width: '1px',
              height: '100%',
              background: this.state.isDragging ? Colors.accentGray() : Colors.keylineDefault(),
            }}
          />
        </div>
        <div className={styles.headerLabel}>{this.props.children}</div>
      </div>
    );
  }
}

export const Headers = () => {
  const widths = React.useContext(ColumnWidthsContext);
  return (
    <div className={styles.headersContainer}>
      <Header
        width={widths.timestamp}
        onResize={(width) => widths.onChange({...widths, timestamp: width})}
      >
        Timestamp
      </Header>
      <Header width={widths.solid} onResize={(width) => widths.onChange({...widths, solid: width})}>
        Op
      </Header>
      <Header
        width={widths.eventType}
        onResize={(width) => widths.onChange({...widths, eventType: width})}
      >
        Event Type
      </Header>
      <div className={styles.infoContainer} style={{flex: 1}}>
        Info
      </div>
    </div>
  );
};
