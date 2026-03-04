import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import {RecoilRoot} from 'recoil';

import {Route} from '../../../app/Route';
import {AnalyticsContext} from '../../../app/analytics';
import {
  buildInstigationEvent,
  buildInstigationEventConnection,
  buildPartitionBackfill,
} from '../../../graphql/types';
import {REFRESHING_DATA} from '../../../live-data-provider/LiveDataRefreshButton';
import {buildQueryMock} from '../../../testing/mocking';
import {BACKFILL_LOGS_PAGE_QUERY, BackfillLogsTab} from '../BackfillLogsTab';

const mockBackfillId = 'mockBackfillId';

const mocks = [
  buildQueryMock({
    query: BACKFILL_LOGS_PAGE_QUERY,
    variables: {backfillId: mockBackfillId, cursor: undefined},
    delay: 10,
    data: {
      partitionBackfillOrError: buildPartitionBackfill({
        logEvents: buildInstigationEventConnection({
          hasMore: true,
          cursor: 'next-cursor-value',
          events: [
            buildInstigationEvent({
              message: 'Event 1',
              timestamp: '1717962300001',
            }),
            buildInstigationEvent({
              message: 'Event 2',
              timestamp: '1717962300002',
            }),
          ],
        }),
      }),
    },
  }),
  buildQueryMock({
    query: BACKFILL_LOGS_PAGE_QUERY,
    variables: {backfillId: mockBackfillId, cursor: 'next-cursor-value'},
    delay: 10,
    data: {
      partitionBackfillOrError: buildPartitionBackfill({
        logEvents: buildInstigationEventConnection({
          hasMore: false,
          cursor: 'final-cursor-value',
          events: [
            buildInstigationEvent({
              message: 'Event 3',
              timestamp: `1717962300003`,
            }),
            buildInstigationEvent({
              message: 'Event 4',
              timestamp: `1717962300004`,
            }),
          ],
        }),
      }),
    },
  }),
];

describe('BackfillLogsTab', () => {
  it('paginates through the logs to load them all', async () => {
    render(
      <RecoilRoot>
        <AnalyticsContext.Provider value={{page: () => {}} as any}>
          <MemoryRouter initialEntries={[`/backfills/${mockBackfillId}?tab=logs`]}>
            <Route path="/backfills/:backfillId">
              <MockedProvider mocks={mocks}>
                <BackfillLogsTab backfill={buildPartitionBackfill({id: mockBackfillId})} />
              </MockedProvider>
            </Route>
          </MemoryRouter>
        </AnalyticsContext.Provider>
      </RecoilRoot>,
    );

    expect(await screen.findByText(REFRESHING_DATA)).toBeVisible();

    waitFor(async () => {
      expect(await screen.findByText('Event 1')).toBeVisible();
      expect(await screen.findByText('Event 4')).toBeVisible();
    });

    waitFor(async () => {
      expect(await screen.findByText(REFRESHING_DATA)).not.toBeVisible();
    });
  });
});
