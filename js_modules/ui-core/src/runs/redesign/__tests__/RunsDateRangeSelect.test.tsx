import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import {TimeContext, TimeContextValue} from '../../../app/time/TimeContext';
import {DialogProps} from '../../../ui/DateRangeDialog';
import {RunFilterToken} from '../../RunsFilterUtils';
import {RunsDateRangeSelect} from '../RunsDateRangeSelect';

jest.mock('../../../ui/DateRangeDialog', () => ({
  DateRangeDialog: ({isOpen, onCancel, onApply}: DialogProps) =>
    isOpen ? (
      <div role="dialog" aria-label="Select a date range">
        <button onClick={onCancel}>Cancel</button>
        <button onClick={() => onApply([1700000000000, 1700086399999])}>Apply</button>
      </div>
    ) : null,
}));

// Tuesday, March 10, 2026, 11:00 in New York (daylight time began on March 8).
const NOW_MS = Date.UTC(2026, 2, 10, 15);

const TIME_CONTEXT = {
  timezone: ['America/New_York', () => 'America/New_York', () => {}],
  resolvedTimezone: 'America/New_York',
  hourCycle: ['Automatic', () => 'Automatic', () => {}],
} as const satisfies TimeContextValue;

const seconds = (ms: number) => `${ms / 1000}`;

const afterToken = (ms: number): RunFilterToken => ({
  token: 'created_date_after',
  value: seconds(ms),
});

const beforeToken = (ms: number): RunFilterToken => ({
  token: 'created_date_before',
  value: seconds(ms),
});

// The preset steps back 7 x 24 hours from today's start, so it lands an hour off New York midnight.
const LAST_7_DAYS_START = Date.UTC(2026, 2, 3, 4);
const MARCH_8_START = Date.UTC(2026, 2, 8, 5);
const MARCH_8_END = Date.UTC(2026, 2, 9, 4) - 1;
const MARCH_10_START = Date.UTC(2026, 2, 10, 4);

const renderSelect = (tokens: RunFilterToken[] = [], onChange = jest.fn()) => {
  render(
    <TimeContext.Provider value={TIME_CONTEXT}>
      <RunsDateRangeSelect tokens={tokens} onChange={onChange} />
    </TimeContext.Provider>,
  );
  return onChange;
};

const findButton = (label: string) => screen.findByRole('button', {name: `Created date: ${label}`});

const pickItem = async (name: string) => {
  const user = userEvent.setup();
  await user.click(await screen.findByRole('button', {name: /^Created date:/}));
  await user.click(await screen.findByRole('menuitem', {name}));
};

describe('RunsDateRangeSelect', () => {
  beforeEach(() => {
    jest.spyOn(Date, 'now').mockReturnValue(NOW_MS);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it.each([
    {name: 'no bounds', tokens: [], label: 'All time'},
    {name: 'today', tokens: [afterToken(MARCH_10_START)], label: 'Today'},
    {
      name: 'yesterday',
      tokens: [afterToken(Date.UTC(2026, 2, 9, 4)), beforeToken(MARCH_10_START)],
      label: 'Yesterday',
    },
    {name: 'the last 7 days', tokens: [afterToken(LAST_7_DAYS_START)], label: 'Within last 7 days'},
    {
      name: 'only a start',
      tokens: [afterToken(Date.UTC(2026, 2, 1, 5))],
      label: 'After Mar 1, 2026',
    },
    {
      name: 'only an end',
      tokens: [beforeToken(Date.UTC(2026, 2, 1, 5))],
      label: 'Before Mar 1, 2026',
    },
    {
      name: 'a day with a daylight time change',
      tokens: [afterToken(MARCH_8_START), beforeToken(MARCH_8_END)],
      label: 'Mar 8, 2026',
    },
    {
      name: 'two different days',
      tokens: [afterToken(Date.UTC(2026, 2, 1, 5)), beforeToken(Date.UTC(2026, 2, 6, 5) - 1)],
      label: 'Mar 1, 2026 - Mar 5, 2026',
    },
    {
      name: 'bounds outside the range a date can hold',
      tokens: [afterToken(8640000000001000), beforeToken(-8640000000001000)],
      label: 'All time',
    },
    {name: 'a bound that is not a number', tokens: [beforeToken(NaN)], label: 'All time'},
    {
      name: 'repeated bounds, where the last one wins',
      tokens: [
        afterToken(Date.UTC(2026, 0, 1, 5)),
        afterToken(Date.UTC(2026, 2, 1, 5)),
        beforeToken(Date.UTC(2026, 2, 6, 5) - 1),
        beforeToken(Date.UTC(2026, 2, 5, 5) - 1),
      ],
      label: 'Mar 1, 2026 - Mar 4, 2026',
    },
  ])('labels $name as "$label"', async ({tokens, label}) => {
    renderSelect(tokens);

    expect(await findButton(label)).toBeVisible();
  });

  it('writes a preset as fixed timestamps and closes the menu', async () => {
    const onChange = renderSelect([]);

    await pickItem('Within last 7 days');

    expect(onChange).toHaveBeenCalledWith([afterToken(LAST_7_DAYS_START)]);
    await waitFor(() => expect(screen.queryByRole('menuitem')).not.toBeInTheDocument());
  });

  it('writes both bounds for a preset that has an end', async () => {
    const onChange = renderSelect([]);

    await pickItem('Yesterday');

    expect(onChange).toHaveBeenCalledWith([
      afterToken(Date.UTC(2026, 2, 9, 4)),
      beforeToken(MARCH_10_START),
    ]);
  });

  it('clears the tokens for all time', async () => {
    const onChange = renderSelect([afterToken(MARCH_10_START)]);

    await pickItem('All time');

    expect(onChange).toHaveBeenCalledWith([]);
  });

  it('writes a custom range with its exact end of day', async () => {
    const user = userEvent.setup();
    const onChange = renderSelect([]);

    await pickItem('Custom…');
    await waitFor(() => expect(screen.queryByRole('menuitem')).not.toBeInTheDocument());
    await user.click(await screen.findByRole('button', {name: 'Apply'}));

    expect(onChange).toHaveBeenCalledWith([
      {token: 'created_date_after', value: '1700000000'},
      {token: 'created_date_before', value: '1700086399.999'},
    ]);
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  });

  it('reopens the custom range dialog after cancelling it', async () => {
    const user = userEvent.setup();
    const onChange = renderSelect([]);

    await pickItem('Custom…');
    await user.click(await screen.findByRole('button', {name: 'Cancel'}));
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    await pickItem('Custom…');

    expect(await screen.findByRole('dialog')).toBeVisible();
    expect(onChange).not.toHaveBeenCalled();
  });
});
