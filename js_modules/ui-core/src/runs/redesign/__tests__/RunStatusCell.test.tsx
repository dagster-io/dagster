import {MockedProvider} from '@apollo/client/testing';
import {act, render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {ReactNode} from 'react';
import {MemoryRouter} from 'react-router-dom';

import {ApolloClient, ApolloLink, ApolloProvider, InMemoryCache} from '../../../apollo-client';
import {BulkActionStatus, RunStatus} from '../../../graphql/types';
import {RunStatusCell} from '../RunStatusCell';
import {
  FIXTURE_NOW_MS,
  assetBackfill,
  backfillEntry,
  canceledRun,
  cancelingRun,
  failedRun,
  failedToStartRun,
  failedWillRetryRun,
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

const wrap = (children: ReactNode) => (
  <MemoryRouter>
    <MockedProvider mocks={[]}>{children}</MockedProvider>
  </MemoryRouter>
);

const renderCells = (children: ReactNode) => {
  const {rerender} = render(wrap(children));
  return {rerenderCells: (next: ReactNode) => rerender(wrap(next))};
};

describe('RunStatusCell', () => {
  describe('with a pinned clock', () => {
    beforeEach(() => {
      jest.useFakeTimers();
      jest.setSystemTime(SYSTEM_TIME_MS);
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it.each([
      ['Not started', notStartedRun],
      ['Queued', queuedRun],
      ['Starting', startingRun],
      ['Started', startedRun],
      ['Managed', managedRun],
      ['Canceling', cancelingRun],
      ['Success', succeededRun],
      ['Failed', failedRun],
      ['Canceled', canceledRun],
    ])('names the %s status on its icon', async (label, entry) => {
      renderCells(<RunStatusCell entry={entry} />);
      expect(await screen.findByRole('img', {name: label})).toBeVisible();
    });

    it('uses the replay treatment for a failure with a queued retry', async () => {
      renderCells(<RunStatusCell entry={failedWillRetryRun} />);
      expect(await screen.findByRole('img', {name: 'Failed (will retry)'})).toBeVisible();
      expect(await screen.findByRole('img', {name: 'replay'})).toBeVisible();
    });

    it('describes a backfill with its own state vocabulary', async () => {
      renderCells(<RunStatusCell entry={assetBackfill} />);
      expect(await screen.findByRole('img', {name: 'Completed'})).toBeVisible();
    });

    it('keeps a failing backfill live until its runs finish canceling', async () => {
      const backfill = {
        backfillStatus: BulkActionStatus.FAILING,
        runStatus: RunStatus.FAILURE,
        startTime: FIXTURE_NOW_MS / 1000 - 10,
        endTime: null,
      };
      const {rerenderCells} = renderCells(<RunStatusCell entry={backfillEntry(backfill)} />);

      expect(await screen.findByRole('img', {name: 'Failing'})).toBeVisible();
      const elapsed = await screen.findByText(CLOCK);
      expect(elapsed).toHaveTextContent('00:00:10');
      act(() => jest.advanceTimersByTime(1000));
      expect(elapsed).toHaveTextContent('00:00:11');

      rerenderCells(
        <RunStatusCell
          entry={backfillEntry({
            ...backfill,
            backfillStatus: BulkActionStatus.FAILED,
            endTime: Date.now() / 1000,
          })}
        />,
      );

      expect(await screen.findByRole('img', {name: 'Failed'})).toBeVisible();
      expect(screen.queryByText(CLOCK)).toBeNull();
    });

    it('advances relative text when the minute turns over', async () => {
      renderCells(<RunStatusCell entry={queuedRun} />);
      const relative = await screen.findByText('10m ago');

      act(() => {
        jest.advanceTimersByTime(59_749);
      });
      expect(relative).toHaveTextContent('10m ago');

      act(() => {
        jest.advanceTimersByTime(1);
      });
      expect(relative).toHaveTextContent('11m ago');
    });

    it.each([
      ['a zeroed clock while starting', startingRun, '00:00:00'],
      [
        'an unknown clock when a running entry has no start time',
        startedRunWithoutStartTime,
        '--:--:--',
      ],
    ])('shows %s and does not tick', async (_name, entry, text) => {
      renderCells(<RunStatusCell entry={entry} />);
      const clock = await screen.findByText(text);

      act(() => {
        jest.advanceTimersByTime(2000);
      });
      expect(clock).toHaveTextContent(text);
    });

    it('advances the live counter on the second boundary', async () => {
      renderCells(<RunStatusCell entry={startedRun} />);
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
      const {rerenderCells} = renderCells(<RunStatusCell entry={startedRun} />);
      expect(await screen.findByText(CLOCK)).toBeVisible();

      rerenderCells(<RunStatusCell entry={succeededRun} />);

      expect(screen.queryByText(CLOCK)).toBeNull();
    });

    it('reveals timing details on the first tab stop, skipping the status icon', async () => {
      const user = userEvent.setup({advanceTimers: jest.advanceTimersByTime});
      renderCells(<RunStatusCell entry={succeededRun} />);
      const timing = await screen.findByText('5m ago');

      await user.tab();
      expect(document.activeElement).toBe(timing);
      expect(await screen.findByRole('tooltip')).toHaveTextContent('Ran for 00:04:00');
    });

    it('calls a failure with no start time a failed launch', async () => {
      const user = userEvent.setup({advanceTimers: jest.advanceTimersByTime});
      renderCells(<RunStatusCell entry={failedToStartRun} />);
      await user.hover(await screen.findByText('5m ago'));

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
      renderCells(<RunStatusCell entry={canceledBeforeStart} />);
      await user.hover(await screen.findByText('5m ago'));

      const tooltip = await screen.findByRole('tooltip');
      expect(tooltip).toHaveTextContent('Finished');
      expect(tooltip).not.toHaveTextContent('Started');
      expect(tooltip).not.toHaveTextContent('Ran for');
    });
  });

  describe('step statistics', () => {
    const renderWithOperationLog = (children: ReactNode) => {
      const operations: string[] = [];
      const link = new ApolloLink((operation) => {
        operations.push(operation.operationName);
        return null;
      });
      const client = new ApolloClient({link, cache: new InMemoryCache()});
      render(
        <MemoryRouter>
          <ApolloProvider client={client}>{children}</ApolloProvider>
        </MemoryRouter>,
      );
      return operations;
    };

    it('fetches step statistics once when a run status icon is hovered', async () => {
      const user = userEvent.setup();
      const operations = renderWithOperationLog(<RunStatusCell entry={succeededRun} />);

      await user.hover(await screen.findByRole('img', {name: 'Success'}));
      await waitFor(() => expect(operations).toEqual(['RunStatsQuery']));
    });

    it('does not fetch step statistics for a backfill', async () => {
      const user = userEvent.setup();
      const operations = renderWithOperationLog(
        <>
          <RunStatusCell entry={assetBackfill} />
          <RunStatusCell entry={succeededRun} />
        </>,
      );

      await user.hover(await screen.findByRole('img', {name: 'Completed'}));
      await user.hover(await screen.findByRole('img', {name: 'Success'}));
      await waitFor(() => expect(operations).toEqual(['RunStatsQuery']));
    });
  });
});
