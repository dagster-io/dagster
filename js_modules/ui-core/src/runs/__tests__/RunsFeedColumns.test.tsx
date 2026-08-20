import {act, render, renderHook, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import {
  DEFAULT_RUNS_FEED_COLUMN_SETTINGS,
  RUNS_FEED_COLUMNS,
  RUNS_FEED_COLUMNS_STORAGE_KEY,
  RunsFeedColumnsMenu,
  RunsFeedColumnsProvider,
  buildMinWidth,
  buildTableOverflowStyle,
  buildTemplateColumns,
  useRunsFeedColumnsState,
  validateRunsFeedColumnSettings,
} from '../RunsFeedColumns';

// The proportional layout the table shipped with before columns became configurable.
const LEGACY_TEMPLATE =
  '60px minmax(0, 1.5fr) minmax(0, 1.2fr) minmax(0, 1fr) 140px 170px 120px 132px';

const columnsFor = (...keys: string[]) =>
  RUNS_FEED_COLUMNS.filter((column) => keys.includes(column.key));

describe('buildTemplateColumns', () => {
  it('matches the original layout when no column has been resized', () => {
    expect(buildTemplateColumns(RUNS_FEED_COLUMNS, {})).toBe(LEGACY_TEMPLATE);
  });

  it('uses pixel tracks for resized columns', () => {
    expect(buildTemplateColumns(RUNS_FEED_COLUMNS, {id: 500, target: 240})).toBe(
      '60px 500px 240px minmax(0, 1fr) 140px 170px 120px 132px',
    );
  });

  it('drops tracks for hidden columns', () => {
    expect(buildTemplateColumns(columnsFor('id', 'status'), {})).toBe(
      '60px minmax(0, 1.5fr) 140px 132px',
    );
  });
});

describe('buildMinWidth', () => {
  it('is undefined while the table is still proportional', () => {
    expect(buildMinWidth(RUNS_FEED_COLUMNS, {})).toBeUndefined();
  });

  it('reserves the full pixel width so the table can scroll horizontally', () => {
    const widths = {id: 800, target: 300, launchedBy: 200, status: 140, createdAt: 170};
    // 60 + 132 fixed columns, pixel widths, and `duration` at its minimum.
    expect(buildMinWidth(RUNS_FEED_COLUMNS, widths)).toBe(
      60 + 132 + 800 + 300 + 200 + 140 + 170 + 90,
    );
  });

  it('ignores hidden columns', () => {
    expect(buildMinWidth(columnsFor('id'), {id: 800})).toBe(60 + 132 + 800);
  });
});

describe('buildTableOverflowStyle', () => {
  it('leaves the scrolling table to its own Container', () => {
    expect(buildTableOverflowStyle({scroll: true, minWidth: 1400})).toEqual({
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
    });
  });

  it('clips a non-scrolling table only while it is still proportional', () => {
    expect(buildTableOverflowStyle({scroll: false, minWidth: undefined})).toEqual({
      overflowX: 'hidden',
      overflowY: 'hidden',
    });
  });

  it('gives a non-scrolling table a horizontal scrollport once columns have pixel widths', () => {
    // Without this, resized columns in the schedule/sensor/tick tables are clipped by the
    // wrapper with no way to scroll to them.
    expect(buildTableOverflowStyle({scroll: false, minWidth: 1400})).toEqual({
      overflowX: 'auto',
      overflowY: 'hidden',
    });
  });
});

describe('validateRunsFeedColumnSettings', () => {
  it('falls back to defaults for missing or malformed values', () => {
    expect(validateRunsFeedColumnSettings(undefined)).toEqual(DEFAULT_RUNS_FEED_COLUMN_SETTINGS);
    expect(validateRunsFeedColumnSettings('nope')).toEqual(DEFAULT_RUNS_FEED_COLUMN_SETTINGS);
    expect(validateRunsFeedColumnSettings({hidden: 'id', widths: 4})).toEqual({
      hidden: [],
      widths: {},
    });
  });

  it('drops unknown columns and non-numeric widths', () => {
    expect(
      validateRunsFeedColumnSettings({
        hidden: ['status', 'notARealColumn'],
        widths: {id: 400, notARealColumn: 100, target: 'wide'},
      }),
    ).toEqual({hidden: ['status'], widths: {id: 400}});
  });

  it('clamps widths to the column minimum and maximum', () => {
    expect(validateRunsFeedColumnSettings({widths: {id: 10, duration: 99999}})).toEqual({
      hidden: [],
      widths: {id: 120, duration: 1200},
    });
  });

  it('never hides every column', () => {
    const settings = validateRunsFeedColumnSettings({
      hidden: RUNS_FEED_COLUMNS.map((column) => column.key),
    });
    expect(settings.hidden).toHaveLength(RUNS_FEED_COLUMNS.length - 1);
  });
});

describe('useRunsFeedColumnsState', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('persists hidden columns and widths across mounts', () => {
    const first = renderHook(() => useRunsFeedColumnsState());
    act(() => {
      first.result.current.toggleColumn('launchedBy');
    });
    act(() => {
      first.result.current.beginResize({id: 300});
      first.result.current.setColumnWidth('id', 640);
      first.result.current.endResize();
    });

    expect(first.result.current.visibleColumns.map((column) => column.key)).toEqual([
      'id',
      'target',
      'status',
      'createdAt',
      'duration',
    ]);
    expect(first.result.current.templateColumns).toContain('640px');

    first.unmount();

    const second = renderHook(() => useRunsFeedColumnsState());
    expect(second.result.current.widths.id).toBe(640);
    expect(second.result.current.isVisible('launchedBy')).toBe(false);
  });

  it('does not write to storage until a resize ends', () => {
    const {result} = renderHook(() => useRunsFeedColumnsState());
    act(() => {
      result.current.beginResize({id: 300});
      result.current.setColumnWidth('id', 500);
    });

    expect(result.current.widths.id).toBe(500);
    expect(window.localStorage.getItem(RUNS_FEED_COLUMNS_STORAGE_KEY)).toBeNull();

    act(() => {
      result.current.endResize();
    });
    expect(window.localStorage.getItem(RUNS_FEED_COLUMNS_STORAGE_KEY)).toContain('500');
  });

  it('clamps a resize to the column minimum', () => {
    const {result} = renderHook(() => useRunsFeedColumnsState());
    act(() => {
      result.current.beginResize({status: 140});
      result.current.setColumnWidth('status', 10);
      result.current.endResize();
    });
    expect(result.current.widths.status).toBe(90);
  });

  it('resets back to the default layout', () => {
    const {result} = renderHook(() => useRunsFeedColumnsState());
    act(() => {
      result.current.toggleColumn('duration');
      result.current.beginResize({id: 300});
      result.current.setColumnWidth('id', 700);
      result.current.endResize();
    });
    act(() => {
      result.current.resetToDefaults();
    });

    expect(result.current.templateColumns).toBe(LEGACY_TEMPLATE);
    expect(result.current.minWidth).toBeUndefined();
  });
});

describe('RunsFeedColumnsMenu', () => {
  const Test = () => {
    const columns = useRunsFeedColumnsState();
    return (
      <RunsFeedColumnsProvider value={columns}>
        <RunsFeedColumnsMenu />
        <div data-testid="visible">
          {columns.visibleColumns.map((column) => column.key).join(',')}
        </div>
      </RunsFeedColumnsProvider>
    );
  };

  beforeEach(() => {
    window.localStorage.clear();
  });

  it('toggles a column off and back on', async () => {
    render(<Test />);
    await userEvent.click(screen.getByRole('button', {name: /columns/i}));

    await userEvent.click(await screen.findByText('Launched by'));
    expect(screen.getByTestId('visible')).toHaveTextContent('id,target,status,createdAt,duration');

    await userEvent.click(screen.getByText('Launched by'));
    expect(screen.getByTestId('visible')).toHaveTextContent(
      'id,target,launchedBy,status,createdAt,duration',
    );
  });
});
