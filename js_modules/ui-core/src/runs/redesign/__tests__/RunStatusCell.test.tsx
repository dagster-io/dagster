import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
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
  failedWillRetryRun,
  managedRun,
  notStartedRun,
  queuedRun,
  startedRun,
  startingRun,
  succeededRun,
} from '../__fixtures__/RunsFeedEntries.fixtures';

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
      jest.setSystemTime(FIXTURE_NOW_MS);
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

    it('calls a backfill Failing while its runs finish canceling', async () => {
      const backfill = {
        backfillStatus: BulkActionStatus.FAILING,
        runStatus: RunStatus.FAILURE,
        startTime: FIXTURE_NOW_MS / 1000 - 10,
        endTime: null,
      };
      const {rerenderCells} = renderCells(<RunStatusCell entry={backfillEntry(backfill)} />);
      expect(await screen.findByRole('img', {name: 'Failing'})).toBeVisible();

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
    });

    it('adds no tab stop for the status icon', async () => {
      const user = userEvent.setup({advanceTimers: jest.advanceTimersByTime});
      renderCells(<RunStatusCell entry={succeededRun} />);
      await screen.findByRole('img', {name: 'Success'});

      await user.tab();
      expect(document.body).toHaveFocus();
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
