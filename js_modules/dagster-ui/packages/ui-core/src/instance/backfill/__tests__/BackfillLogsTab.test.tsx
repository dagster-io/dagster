import {MockedProvider} from '@apollo/client/testing';
import {render, screen} from '@testing-library/react';
import {MemoryRouter, Route} from 'react-router-dom';
import {RecoilRoot} from 'recoil';

import {AnalyticsContext} from '../../../app/analytics';
import {
  buildInstigationEvent,
  buildInstigationEventConnection,
  buildPartitionBackfill,
} from '../../../graphql/types';
import {BACKFILL_LOGS_PAGE_QUERY, BackfillLogsTab} from '../BackfillLogsTab';

// This file must be mocked because Jest can't handle `import.meta.url`.
jest.mock('../../../graph/asyncGraphLayout', () => ({}));
jest.mock('../../../app/QueryRefresh', () => {
  return {
    useQueryRefreshAtInterval: jest.fn(),
    QueryRefreshCountdown: jest.fn(() => <div />),
  };
});

const mockBackfillId = 'mockBackfillId';

const mocks = [
  {
    request: {
      query: BACKFILL_LOGS_PAGE_QUERY,
      variables: {backfillId: mockBackfillId, cursor: undefined},
    },
    delay: 10,
    result: {
      __typename: 'CloudQuery',
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
    },
  },
  {
    request: {
      query: BACKFILL_LOGS_PAGE_QUERY,
      variables: {backfillId: mockBackfillId, cursor: 'next-cursor-value'},
    },
    delay: 10,
    result: {
      __typename: 'CloudQuery',
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
    },
  },
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

    expect(await screen.findByText('Event 1')).toBeVisible();
    expect(await screen.findByText('Event 4')).toBeVisible();
  });
});
