import {Button, Icon, Menu, MenuDivider, MenuItem, Popover} from '@dagster-io/ui-components';
import clsx from 'clsx';
import * as React from 'react';

import styles from './css/RunsFeedColumns.module.css';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

export type RunsFeedColumnKey =
  | 'id'
  | 'target'
  | 'launchedBy'
  | 'status'
  | 'createdAt'
  | 'duration';

export interface RunsFeedColumnConfig {
  key: RunsFeedColumnKey;
  label: string;
  // The grid track used before the column has ever been resized, preserving the
  // proportional layout the table has always shipped with.
  defaultTrack: string;
  // The pixel width used when the column is seeded into pixel mode while hidden,
  // and when its width is reset.
  defaultWidth: number;
  minWidth: number;
}

// The checkbox and actions columns are always present and are not resizable.
export const CHECKBOX_COLUMN_TRACK = '60px';
export const ACTIONS_COLUMN_TRACK = '132px';
const FIXED_COLUMNS_WIDTH = 60 + 132;

const MAX_COLUMN_WIDTH = 1200;

export const RUNS_FEED_COLUMNS: RunsFeedColumnConfig[] = [
  {key: 'id', label: 'ID', defaultTrack: 'minmax(0, 1.5fr)', defaultWidth: 320, minWidth: 120},
  {
    key: 'target',
    label: 'Target',
    defaultTrack: 'minmax(0, 1.2fr)',
    defaultWidth: 260,
    minWidth: 120,
  },
  {
    key: 'launchedBy',
    label: 'Launched by',
    defaultTrack: 'minmax(0, 1fr)',
    defaultWidth: 220,
    minWidth: 120,
  },
  {key: 'status', label: 'Status', defaultTrack: '140px', defaultWidth: 140, minWidth: 90},
  {key: 'createdAt', label: 'Created at', defaultTrack: '170px', defaultWidth: 170, minWidth: 120},
  {key: 'duration', label: 'Duration', defaultTrack: '120px', defaultWidth: 120, minWidth: 90},
];

const COLUMNS_BY_KEY: Record<RunsFeedColumnKey, RunsFeedColumnConfig> = Object.fromEntries(
  RUNS_FEED_COLUMNS.map((column) => [column.key, column]),
) as Record<RunsFeedColumnKey, RunsFeedColumnConfig>;

export type RunsFeedColumnWidths = Partial<Record<RunsFeedColumnKey, number>>;

export interface RunsFeedColumnSettings {
  hidden: RunsFeedColumnKey[];
  widths: RunsFeedColumnWidths;
}

export const DEFAULT_RUNS_FEED_COLUMN_SETTINGS: RunsFeedColumnSettings = {hidden: [], widths: {}};

export const RUNS_FEED_COLUMNS_STORAGE_KEY = 'runs-feed-columns';

const clampWidth = (column: RunsFeedColumnConfig, width: number) =>
  Math.round(Math.min(MAX_COLUMN_WIDTH, Math.max(column.minWidth, width)));

/**
 * localStorage is user-editable and settings written by a newer version of the app may
 * mention columns that no longer exist, so drop anything we don't recognize.
 */
export const validateRunsFeedColumnSettings = (json: any): RunsFeedColumnSettings => {
  if (!json || typeof json !== 'object') {
    return DEFAULT_RUNS_FEED_COLUMN_SETTINGS;
  }

  const hidden = Array.isArray(json.hidden)
    ? RUNS_FEED_COLUMNS.filter((column) => json.hidden.includes(column.key)).map(
        (column) => column.key,
      )
    : [];

  const widths: RunsFeedColumnWidths = {};
  if (json.widths && typeof json.widths === 'object') {
    for (const column of RUNS_FEED_COLUMNS) {
      const width = json.widths[column.key];
      if (typeof width === 'number' && Number.isFinite(width)) {
        widths[column.key] = clampWidth(column, width);
      }
    }
  }

  // Never allow every column to be hidden, otherwise the table has nothing to show.
  if (hidden.length === RUNS_FEED_COLUMNS.length) {
    return {hidden: hidden.slice(1), widths};
  }

  return {hidden, widths};
};

export const buildTemplateColumns = (
  visibleColumns: RunsFeedColumnConfig[],
  widths: RunsFeedColumnWidths,
) => {
  const tracks = visibleColumns.map((column) => {
    const width = widths[column.key];
    return width === undefined ? column.defaultTrack : `${width}px`;
  });
  return [CHECKBOX_COLUMN_TRACK, ...tracks, ACTIONS_COLUMN_TRACK].join(' ');
};

/**
 * Once columns have pixel widths the table is allowed to be wider than its container,
 * which is what makes a widened ID or Target column useful. Returns the width the rows
 * and header must reserve, or undefined while the table is still proportional.
 */
export const buildMinWidth = (
  visibleColumns: RunsFeedColumnConfig[],
  widths: RunsFeedColumnWidths,
) => {
  if (!visibleColumns.some((column) => widths[column.key] !== undefined)) {
    return undefined;
  }
  return visibleColumns.reduce(
    (total, column) => total + (widths[column.key] ?? column.minWidth),
    FIXED_COLUMNS_WIDTH,
  );
};

/**
 * Pixel widths let the table exceed its container, so something has to provide the
 * horizontal scrollport. With `scroll` the table's own Container does. Without it (the
 * schedule/sensor/tick tables) and in the empty state (which renders no Container at
 * all), the wrapper must, or widened columns are clipped and unreachable.
 */
export const buildTableOverflowStyle = ({
  scroll,
  minWidth,
}: {
  scroll: boolean;
  minWidth: number | undefined;
}): React.CSSProperties =>
  scroll
    ? {overflow: 'hidden', display: 'flex', flexDirection: 'column'}
    : {overflowX: minWidth === undefined ? 'hidden' : 'auto', overflowY: 'hidden'};

interface RunsFeedColumnsState {
  columns: RunsFeedColumnConfig[];
  visibleColumns: RunsFeedColumnConfig[];
  templateColumns: string;
  minWidth: number | undefined;
  widths: RunsFeedColumnWidths;
  isVisible: (key: RunsFeedColumnKey) => boolean;
  toggleColumn: (key: RunsFeedColumnKey) => void;
  resetToDefaults: () => void;
  resetColumnWidth: (key: RunsFeedColumnKey) => void;
  /** Enter pixel mode with the widths currently rendered, so resizing doesn't jump. */
  beginResize: (measuredWidths: RunsFeedColumnWidths) => void;
  setColumnWidth: (key: RunsFeedColumnKey, width: number) => void;
  endResize: () => void;
}

const defaultVisibleColumns = RUNS_FEED_COLUMNS;

const DEFAULT_STATE: RunsFeedColumnsState = {
  columns: RUNS_FEED_COLUMNS,
  visibleColumns: defaultVisibleColumns,
  templateColumns: buildTemplateColumns(defaultVisibleColumns, {}),
  minWidth: undefined,
  widths: {},
  isVisible: () => true,
  toggleColumn: () => {},
  resetToDefaults: () => {},
  resetColumnWidth: () => {},
  beginResize: () => {},
  setColumnWidth: () => {},
  endResize: () => {},
};

export const RunsFeedColumnsContext = React.createContext<RunsFeedColumnsState>(DEFAULT_STATE);

export const useRunsFeedColumns = () => React.useContext(RunsFeedColumnsContext);

export const useRunsFeedColumnsState = (): RunsFeedColumnsState => {
  const [settings, setSettings] = useStateWithStorage(
    RUNS_FEED_COLUMNS_STORAGE_KEY,
    validateRunsFeedColumnSettings,
  );

  // While dragging we keep widths in component state and only write to localStorage when
  // the drag ends, so a resize doesn't produce a write per mouse move.
  const [dragWidths, setDragWidths] = React.useState<RunsFeedColumnWidths | null>(null);
  const dragWidthsRef = React.useRef<RunsFeedColumnWidths | null>(null);

  const hidden = settings.hidden;
  const widths = dragWidths ?? settings.widths;

  const visibleColumns = React.useMemo(
    () => RUNS_FEED_COLUMNS.filter((column) => !hidden.includes(column.key)),
    [hidden],
  );

  const templateColumns = React.useMemo(
    () => buildTemplateColumns(visibleColumns, widths),
    [visibleColumns, widths],
  );

  const minWidth = React.useMemo(
    () => buildMinWidth(visibleColumns, widths),
    [visibleColumns, widths],
  );

  const isVisible = React.useCallback((key: RunsFeedColumnKey) => !hidden.includes(key), [hidden]);

  const toggleColumn = React.useCallback(
    (key: RunsFeedColumnKey) => {
      setSettings((current) => {
        const isHidden = current.hidden.includes(key);
        if (!isHidden && current.hidden.length === RUNS_FEED_COLUMNS.length - 1) {
          // Keep at least one column visible.
          return current;
        }
        return {
          ...current,
          hidden: isHidden
            ? current.hidden.filter((hiddenKey) => hiddenKey !== key)
            : [...current.hidden, key],
        };
      });
    },
    [setSettings],
  );

  const resetToDefaults = React.useCallback(() => {
    dragWidthsRef.current = null;
    setDragWidths(null);
    setSettings(DEFAULT_RUNS_FEED_COLUMN_SETTINGS);
  }, [setSettings]);

  const resetColumnWidth = React.useCallback(
    (key: RunsFeedColumnKey) => {
      setSettings((current) => {
        const nextWidths = {...current.widths};
        // If other columns are in pixel mode, fall back to this column's default pixel
        // width; a lone `fr` track next to pixel tracks would collapse.
        if (Object.keys(nextWidths).length > 1) {
          nextWidths[key] = COLUMNS_BY_KEY[key].defaultWidth;
        } else {
          delete nextWidths[key];
        }
        return {...current, widths: nextWidths};
      });
      dragWidthsRef.current = null;
      setDragWidths(null);
    },
    [setSettings],
  );

  const beginResize = React.useCallback((measuredWidths: RunsFeedColumnWidths) => {
    dragWidthsRef.current = measuredWidths;
    setDragWidths(measuredWidths);
  }, []);

  const setColumnWidth = React.useCallback((key: RunsFeedColumnKey, width: number) => {
    const next = {
      ...(dragWidthsRef.current ?? {}),
      [key]: clampWidth(COLUMNS_BY_KEY[key], width),
    };
    dragWidthsRef.current = next;
    setDragWidths(next);
  }, []);

  const endResize = React.useCallback(() => {
    const finalWidths = dragWidthsRef.current;
    dragWidthsRef.current = null;
    setDragWidths(null);
    if (finalWidths) {
      setSettings((current) => ({...current, widths: finalWidths}));
    }
  }, [setSettings]);

  return React.useMemo(
    () => ({
      columns: RUNS_FEED_COLUMNS,
      visibleColumns,
      templateColumns,
      minWidth,
      widths,
      isVisible,
      toggleColumn,
      resetToDefaults,
      resetColumnWidth,
      beginResize,
      setColumnWidth,
      endResize,
    }),
    [
      visibleColumns,
      templateColumns,
      minWidth,
      widths,
      isVisible,
      toggleColumn,
      resetToDefaults,
      resetColumnWidth,
      beginResize,
      setColumnWidth,
      endResize,
    ],
  );
};

export const RunsFeedColumnsProvider = ({
  value,
  children,
}: {
  value: RunsFeedColumnsState;
  children: React.ReactNode;
}) => <RunsFeedColumnsContext.Provider value={value}>{children}</RunsFeedColumnsContext.Provider>;

export const RunsFeedColumnsMenu = () => {
  const {columns, isVisible, toggleColumn, resetToDefaults, visibleColumns} = useRunsFeedColumns();
  const isLastVisible = visibleColumns.length === 1;

  return (
    <Popover
      placement="bottom-end"
      content={
        <Menu>
          {columns.map((column) => {
            const visible = isVisible(column.key);
            return (
              <MenuItem
                key={column.key}
                text={column.label}
                icon={visible ? 'checkbox_checked' : 'checkbox_empty'}
                disabled={visible && isLastVisible}
                onClick={() => toggleColumn(column.key)}
              />
            );
          })}
          <MenuDivider />
          <MenuItem text="Reset columns" icon="settings_backup_restore" onClick={resetToDefaults} />
        </Menu>
      }
    >
      <Button icon={<Icon name="table_columns" />} rightIcon={<Icon name="expand_more" />}>
        Columns
      </Button>
    </Popover>
  );
};

/**
 * Drag handle rendered at the trailing edge of a resizable header cell. On drag start we
 * measure every rendered column so the table can switch from proportional to pixel widths
 * without the layout shifting under the cursor.
 */
export const ColumnResizeHandle = ({columnKey}: {columnKey: RunsFeedColumnKey}) => {
  const {visibleColumns, widths, beginResize, setColumnWidth, endResize, resetColumnWidth} =
    useRunsFeedColumns();
  const [isDragging, setIsDragging] = React.useState(false);
  const dragState = React.useRef<{startX: number; startWidth: number} | null>(null);
  const handleRef = React.useRef<HTMLDivElement>(null);

  const measureRenderedWidths = React.useCallback((): RunsFeedColumnWidths => {
    const measured: RunsFeedColumnWidths = {};
    const headerRow = handleRef.current?.parentElement?.parentElement;
    // Header cells are the grid children: [checkbox, ...visibleColumns, actions].
    const cells = headerRow ? Array.from(headerRow.children) : [];
    visibleColumns.forEach((column, index) => {
      const cell = cells[index + 1];
      const rendered = cell?.getBoundingClientRect().width;
      measured[column.key] = Math.round(
        rendered && rendered > 0 ? rendered : (widths[column.key] ?? column.defaultWidth),
      );
    });
    // Hidden columns keep a pixel width too, so unhiding one doesn't mix `fr` and `px`.
    RUNS_FEED_COLUMNS.forEach((column) => {
      if (measured[column.key] === undefined) {
        measured[column.key] = widths[column.key] ?? column.defaultWidth;
      }
    });
    return measured;
  }, [visibleColumns, widths]);

  const onPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();

    const measured = measureRenderedWidths();
    const startWidth = measured[columnKey] ?? COLUMNS_BY_KEY[columnKey].defaultWidth;
    dragState.current = {startX: e.clientX, startWidth};

    e.currentTarget.setPointerCapture(e.pointerId);
    beginResize(measured);
    setIsDragging(true);
  };

  const onPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    const drag = dragState.current;
    if (!drag) {
      return;
    }
    setColumnWidth(columnKey, drag.startWidth + (e.clientX - drag.startX));
  };

  const onPointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!dragState.current) {
      return;
    }
    dragState.current = null;
    if (e.currentTarget.hasPointerCapture(e.pointerId)) {
      e.currentTarget.releasePointerCapture(e.pointerId);
    }
    setIsDragging(false);
    endResize();
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') {
      return;
    }
    e.preventDefault();
    const measured = measureRenderedWidths();
    const current = measured[columnKey] ?? COLUMNS_BY_KEY[columnKey].defaultWidth;
    beginResize(measured);
    setColumnWidth(columnKey, current + (e.key === 'ArrowRight' ? 16 : -16));
    endResize();
  };

  return (
    <div
      ref={handleRef}
      role="separator"
      aria-orientation="vertical"
      aria-label={`Resize ${COLUMNS_BY_KEY[columnKey].label} column`}
      tabIndex={0}
      className={clsx(styles.resizeHandle, isDragging && styles.resizeHandleDragging)}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerCancel={onPointerUp}
      onKeyDown={onKeyDown}
      onDoubleClick={() => resetColumnWidth(columnKey)}
    >
      <div />
    </div>
  );
};
