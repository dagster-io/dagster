import {MockedProvider} from '@apollo/client/testing';
import {getAllByText, getByText, render, screen, waitFor} from '@testing-library/react';
import React from 'react';
import {MemoryRouter, Route} from 'react-router-dom';

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
import {BACKFILL_DETAILS_QUERY, BackfillPage} from '../BackfillPage';

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
      query: BACKFILL_DETAILS_QUERY,
      variables: {backfillId: mockBackfillId},
    },
    result: {
      __typename: 'CloudQuery',
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
    },
  },
];

describe('BackfillPage', () => {
  it('renders the loading state', async () => {
    render(
      <AnalyticsContext.Provider value={{page: () => {}} as any}>
        <MemoryRouter initialEntries={[`/backfills/${mockBackfillId}`]}>
          <Route path="/backfills/:backfillId">
            <MockedProvider mocks={mocks}>
              <BackfillPage />
            </MockedProvider>
          </Route>
        </MemoryRouter>
      </AnalyticsContext.Provider>,
    );

    expect(await screen.findByTestId('page-loading-indicator')).toBeInTheDocument();
    expect(await screen.findByText('assetA')).toBeVisible();
  });

  it('renders the error state', async () => {
    const errorMocks = [
      {
        request: {
          query: BACKFILL_DETAILS_QUERY,
          variables: {backfillId: mockBackfillId},
        },
        result: {
          data: {
            __typename: 'CloudQuery',
            partitionBackfillOrError: buildPythonError({
              message: 'An error occurred',
            }),
          },
        },
      },
    ];

    const {getByText} = render(
      <AnalyticsContext.Provider value={{page: () => {}} as any}>
        <MemoryRouter initialEntries={[`/backfills/${mockBackfillId}`]}>
          <Route path="/backfills/:backfillId">
            <MockedProvider mocks={errorMocks}>
              <BackfillPage />
            </MockedProvider>
          </Route>
        </MemoryRouter>
      </AnalyticsContext.Provider>,
    );

    await waitFor(() => expect(getByText('An error occurred')).toBeVisible());
  });

  it('renders the loaded state', async () => {
    render(
      <AnalyticsContext.Provider value={{page: () => {}} as any}>
        <MemoryRouter initialEntries={[`/backfills/${mockBackfillId}`]}>
          <Route path="/backfills/:backfillId">
            <MockedProvider mocks={mocks}>
              <BackfillPage />
            </MockedProvider>
          </Route>
        </MemoryRouter>
      </AnalyticsContext.Provider>,
    );

    // Check if the loaded content is displayed
    const detailRow = await screen.findByTestId('backfill-page-details');

    expect(screen.getByText('Partition selection')).toBeVisible();
    expect(screen.getByText('Asset name')).toBeVisible();

    expect(getByText(detailRow, 'Jan 1, 1970, 12:16:40 AM')).toBeVisible();
    expect(getByText(detailRow, 'In progress')).toBeVisible();

    const assetARow = await screen.findByTestId('backfill-asset-row-assetA');
    // Check if the correct data is displayed
    expect(getByText(assetARow, 'assetA')).toBeVisible();
    expect(getByText(assetARow, '33')).toBeVisible(); // numPartitionsTargeted
    expect(getByText(assetARow, '22')).toBeVisible(); // numPartitionsInProgress
    expect(getByText(assetARow, '11')).toBeVisible(); // numPartitionsMaterialized
    expect(getByText(assetARow, '0')).toBeVisible(); // numPartitionsFailed

    const assetBRow = await screen.findByTestId('backfill-asset-row-assetB');
    expect(getByText(assetBRow, 'assetB')).toBeVisible();
    expect(getByText(assetBRow, 'Completed')).toBeVisible();
    expect(getAllByText(assetBRow, '-').length).toBe(3);
  });
});
