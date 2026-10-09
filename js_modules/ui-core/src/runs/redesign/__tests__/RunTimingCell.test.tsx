import {act, render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {ReactNode} from 'react';

import {BulkActionStatus, RunStatus} from '../../../graphql/types';
import {RunTimingCell} from '../RunTimingCell';
import {
  FIXTURE_NOW_MS,
  backfillEntry,
  failedToStartRun,
  managedRun,
  notStartedRun,
  queuedRun,
  runEntry,
  startedRun,
  startedRunWithoutStartTime,
  startingRun,
  succeededRun,
} from '../__fixtures__/RunsFeedEntries.fixtures';

// A quarter-second offset so the ticker's alignment to the next second boundary is observable.
const SYSTEM_TIME_MS = FIXTURE_NOW_MS + 250;

const CLOCK = /^\d\d:\d\d:\d\d$/;
const PLACEHOLDER_CLOCK = '--:--:--';

const renderCells = (children: ReactNode) => {
  const {rerender} = render(children);
  return {rerenderCells: (next: ReactNode) => rerender(next)};
};

describe('RunTimingCell', () => {
  describe('with a pinned clock', () => {
    beforeEach(() => {
      jest.useFakeTimers();
      jest.setSystemTime(SYSTEM_TIME_MS);
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('keeps a failing backfill counting until its runs finish canceling', async () => {
      const backfill = {
        backfillStatus: BulkActionStatus.FAILING,
        runStatus: RunStatus.FAILURE,
        startTime: FIXTURE_NOW_MS / 1000 - 10,
        endTime: null,
      };
      const {rerenderCells} = renderCells(<RunTimingCell entry={backfillEntry(backfill)} />);

      const elapsed = await screen.findByText(CLOCK);
      expect(elapsed).toHaveTextContent('00:00:10');
      act(() => jest.advanceTimersByTime(1000));
      expect(elapsed).toHaveTextContent('00:00:11');

      rerenderCells(
        <RunTimingCell
          entry={backfillEntry({
            ...backfill,
            backfillStatus: BulkActionStatus.FAILED,
            endTime: Date.now() / 1000,
          })}
        />,
      );

      expect(await screen.findByText('0 sec ago')).toBeVisible();
      expect(screen.queryByText(CLOCK)).toBeNull();
    });

    it('advances relative text when the minute turns over', async () => {
      renderCells(<RunTimingCell entry={succeededRun} />);
      const relative = await screen.findByText('5 min ago');

      act(() => {
        jest.advanceTimersByTime(59_749);
      });
      expect(relative).toHaveTextContent('5 min ago');

      act(() => {
        jest.advanceTimersByTime(1);
      });
      expect(relative).toHaveTextContent('6 min ago');
    });

    it('counts a queued run from its creation', async () => {
      renderCells(<RunTimingCell entry={queuedRun} />);
      const elapsed = await screen.findByText(CLOCK);
      expect(elapsed).toHaveTextContent('00:10:00');

      act(() => {
        jest.advanceTimersByTime(750);
      });
      expect(elapsed).toHaveTextContent('00:10:01');
    });

    it.each([
      ['not started', notStartedRun],
      ['starting', startingRun],
      ['managed', managedRun],
      ['running without a start time', startedRunWithoutStartTime],
    ])('shows an unknown clock that does not tick when %s', async (_name, entry) => {
      renderCells(<RunTimingCell entry={entry} />);
      const clock = await screen.findByText(PLACEHOLDER_CLOCK);

      act(() => {
        jest.advanceTimersByTime(2000);
      });
      expect(clock).toHaveTextContent(PLACEHOLDER_CLOCK);
    });

    it('advances the live counter on the second boundary', async () => {
      renderCells(<RunTimingCell entry={startedRun} />);
      const elapsed = await screen.findByText(CLOCK);
      expect(elapsed).toHaveTextContent('00:00:10');

      act(() => {
        jest.advanceTimersByTime(749);
      });
      expect(elapsed).toHaveTextContent('00:00:10');

      act(() => {
        jest.advanceTimersByTime(1);
      });
      expect(elapsed).toHaveTextContent('00:00:11');

      act(() => {
        jest.advanceTimersByTime(1000);
      });
      expect(elapsed).toHaveTextContent('00:00:12');
    });

    it('stops the live counter when a running entry reaches a terminal state', async () => {
      const {rerenderCells} = renderCells(<RunTimingCell entry={startedRun} />);
      expect(await screen.findByText(CLOCK)).toBeVisible();

      rerenderCells(<RunTimingCell entry={succeededRun} />);

      expect(screen.queryByText(CLOCK)).toBeNull();
    });

    it('reveals timing details on its tab stop', async () => {
      const user = userEvent.setup({advanceTimers: jest.advanceTimersByTime});
      renderCells(<RunTimingCell entry={succeededRun} />);
      const timing = await screen.findByText('5 min ago');

      await user.tab();
      expect(document.activeElement).toBe(timing);
      expect(await screen.findByRole('tooltip')).toHaveTextContent('Ran for 00:04:00');
    });

    it('calls a failure with no start time a failed launch', async () => {
      const user = userEvent.setup({advanceTimers: jest.advanceTimersByTime});
      renderCells(<RunTimingCell entry={failedToStartRun} />);
      await user.hover(await screen.findByText('5 min ago'));

      const tooltip = await screen.findByRole('tooltip');
      expect(tooltip).toHaveTextContent('Failed to start');
      expect(tooltip).not.toHaveTextContent('unavailable');
    });

    it('leaves out missing timing for a terminal entry with no start time', async () => {
      const user = userEvent.setup({advanceTimers: jest.advanceTimersByTime});
      const canceledBeforeStart = runEntry({
        runStatus: RunStatus.CANCELED,
        startTime: null,
        endTime: FIXTURE_NOW_MS / 1000 - 300,
      });
      renderCells(<RunTimingCell entry={canceledBeforeStart} />);
      await user.hover(await screen.findByText('5 min ago'));

      const tooltip = await screen.findByRole('tooltip');
      expect(tooltip).toHaveTextContent('Finished');
      expect(tooltip).not.toHaveTextContent('Started');
      expect(tooltip).not.toHaveTextContent('Ran for');
    });
  });
});
