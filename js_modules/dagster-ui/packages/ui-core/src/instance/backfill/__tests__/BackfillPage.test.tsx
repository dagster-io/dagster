import {MockedProvider} from '@apollo/client/testing';
import {getAllByText, getByText, getByTitle, render, screen, waitFor} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import {RecoilRoot} from 'recoil';

import {Route} from '../../../app/Route';
import {AnalyticsContext} from '../../../app/analytics';
import {
  BulkActionStatus,
  buildAssetBackfillData,
  buildAssetKey,
  buildAssetPartitionsStatusCounts,
  buildPartitionBackfill,
  buildPartitionKeyRange,
  buildPythonError,
  buildUnpartitionedAssetStatus,
} from '../../../graphql/types';
import {
  buildQueryMock,
  mockViewportClientRect,
  restoreViewportClientRect,
} from '../../../testing/mocking';
import {BackfillPage} from '../BackfillPage';
import {BACKFILL_DETAILS_QUERY} from '../useBackfillDetailsQuery';

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
  buildQueryMock({
    query: BACKFILL_DETAILS_QUERY,
    variables: {backfillId: mockBackfillId},
    delay: 10,
    data: {
      partitionBackfillOrError: buildPartitionBackfill({
        assetBackfillData: buildAssetBackfillData({
          rootTargetedPartitions: {
            __typename: 'AssetBackfillTargetPartitions',
            partitionKeys: ['1', '2', '3'],
            ranges: [buildPartitionKeyRange({start: '1', end: '2'})],
          },
          assetBackfillStatuses: [
            {
              ...buildAssetPartitionsStatusCounts({
                assetKey: buildAssetKey({
                  path: ['assetA'],
                }),
                numPartitionsTargeted: 33,
                numPartitionsInProgress: 22,
                numPartitionsMaterialized: 11,
                numPartitionsFailed: 0,
              }),
              __typename: 'AssetPartitionsStatusCounts',
            },
            {
              ...buildUnpartitionedAssetStatus({
                assetKey: buildAssetKey({
                  path: ['assetB'],
                }),
                materialized: true,
                inProgress: false,
                failed: false,
              }),
              __typename: 'UnpartitionedAssetStatus',
            },
          ],
        }),
        endTimestamp: 2000,
        numPartitions: 3,
        status: BulkActionStatus.REQUESTED,
        timestamp: 1000,
      }),
    },
  }),
];

describe('BackfillPage', () => {
  beforeAll(() => {
    mockViewportClientRect();
  });

  afterAll(() => {
    restoreViewportClientRect();
  });

  it('renders the loading state', async () => {
    render(
      <RecoilRoot>
        <AnalyticsContext.Provider value={{page: () => {}} as any}>
          <MemoryRouter initialEntries={[`/backfills/${mockBackfillId}`]}>
            <Route path="/backfills/:backfillId">
              <MockedProvider mocks={mocks}>
                <BackfillPage />
              </MockedProvider>
            </Route>
          </MemoryRouter>
        </AnalyticsContext.Provider>
      </RecoilRoot>,
    );

    expect(await screen.findByTestId('page-loading-indicator')).toBeInTheDocument();
    expect(await screen.findByTitle('assetA')).toBeVisible();
  });

  it('renders the error state', async () => {
    const errorMocks = [
      buildQueryMock({
        query: BACKFILL_DETAILS_QUERY,
        variables: {backfillId: mockBackfillId},
        data: {
          __typename: 'CloudQuery',
          partitionBackfillOrError: buildPythonError({
            message: 'An error occurred',
          }),
        },
      }),
    ];

    const {getByText} = render(
      <RecoilRoot>
        <AnalyticsContext.Provider value={{page: () => {}} as any}>
          <MemoryRouter initialEntries={[`/backfills/${mockBackfillId}`]}>
            <Route path="/backfills/:backfillId">
              <MockedProvider mocks={errorMocks}>
                <BackfillPage />
              </MockedProvider>
            </Route>
          </MemoryRouter>
        </AnalyticsContext.Provider>
      </RecoilRoot>,
    );

    await waitFor(() => expect(getByText('An error occurred')).toBeVisible());
  });

  it('renders the loaded state', async () => {
    render(
      <RecoilRoot>
        <AnalyticsContext.Provider value={{page: () => {}} as any}>
          <MemoryRouter initialEntries={[`/backfills/${mockBackfillId}`]}>
            <Route path="/backfills/:backfillId">
              <MockedProvider mocks={mocks}>
                <BackfillPage />
              </MockedProvider>
            </Route>
          </MemoryRouter>
        </AnalyticsContext.Provider>
      </RecoilRoot>,
    );

    // Check if the loaded content is displayed
    const detailRow = await screen.findByTestId('backfill-page-details');

    expect(screen.getByText('Partition selection')).toBeVisible();
    expect(screen.getByText('Asset name')).toBeVisible();

    expect(getByText(detailRow, 'Jan 1, 1970, 12:16:40 AM')).toBeVisible();
    expect(getByText(detailRow, 'In progress')).toBeVisible();

    const assetARow = await screen.findByTestId('backfill-asset-row-assetA');
    // Check if the correct data is displayed
    expect(getByTitle(assetARow, 'assetA')).toBeVisible();
    expect(getByText(assetARow, '33')).toBeVisible(); // numPartitionsTargeted
    expect(getByText(assetARow, '22')).toBeVisible(); // numPartitionsInProgress
    expect(getByText(assetARow, '11')).toBeVisible(); // numPartitionsMaterialized
    expect(getByText(assetARow, '0')).toBeVisible(); // numPartitionsFailed

    const assetBRow = await screen.findByTestId('backfill-asset-row-assetB');
    expect(getByTitle(assetBRow, 'assetB')).toBeVisible();
    expect(getByText(assetBRow, 'Completed')).toBeVisible();
    expect(getAllByText(assetBRow, '-').length).toBe(3);
  });
});
