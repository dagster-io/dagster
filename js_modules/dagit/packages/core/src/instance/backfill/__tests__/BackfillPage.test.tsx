import {MockedProvider} from '@apollo/client/testing';
import {render, fireEvent, waitFor, screen} from '@testing-library/react';
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
} from '../../../graphql/types';
import {BACKFILL_DETAILS_QUERY, BackfillPage, PartitionSelection} from '../BackfillPage';

const mockBackfillId = 'mockBackfillId';

const mocks = [
  {
    request: {
      query: BACKFILL_DETAILS_QUERY,
      variables: {backfillId: mockBackfillId},
    },
    result: {
      __typename: 'CloudDagitQuery',
      data: {
        partitionBackfillOrError: buildPartitionBackfill({
          assetBackfillData: buildAssetBackfillData({
            rootAssetTargetedPartitions: ['1', '2', '3'],
            rootAssetTargetedRanges: [buildPartitionKeyRange({start: '1', end: '2'})],
            assetBackfillStatuses: [
              buildAssetPartitionsStatusCounts({
                assetKey: buildAssetKey({
                  path: ['assetA'],
                }),
                numPartitionsTargeted: 33,
                numPartitionsInProgress: 22,
                numPartitionsMaterialized: 11,
                numPartitionsFailed: 0,
              }),
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
    const {getByText} = render(
      <AnalyticsContext.Provider value={{page: () => {}} as any}>
        <MemoryRouter initialEntries={[`/backfills/${mockBackfillId}`]}>
          <Route path="/backfills/:backfillId">
            <MockedProvider mocks={mocks} addTypename={false}>
              <BackfillPage />
            </MockedProvider>
          </Route>
        </MemoryRouter>
      </AnalyticsContext.Provider>,
    );

    expect(screen.getByTestId('page-loading-indicator')).toBeInTheDocument();

    await waitFor(() => getByText('assetA'));
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
            __typename: 'CloudDagitQuery',
            partitionBackfillOrError: {
              __typename: 'PythonError',
              message: 'An error occurred',
            },
          },
        },
      },
    ];

    const {getByText} = render(
      <AnalyticsContext.Provider value={{page: () => {}} as any}>
        <MemoryRouter initialEntries={[`/backfills/${mockBackfillId}`]}>
          <Route path="/backfills/:backfillId">
            <MockedProvider mocks={errorMocks} addTypename={false}>
              <BackfillPage />
            </MockedProvider>
          </Route>
        </MemoryRouter>
      </AnalyticsContext.Provider>,
    );

    await waitFor(() => expect(getByText('An error occurred')).toBeVisible());
  });

  it('renders the loaded state', async () => {
    const {getByText, getAllByText} = render(
      <AnalyticsContext.Provider value={{page: () => {}} as any}>
        <MemoryRouter initialEntries={[`/backfills/${mockBackfillId}`]}>
          <Route path="/backfills/:backfillId">
            <MockedProvider mocks={mocks} addTypename={false}>
              <BackfillPage />
            </MockedProvider>
          </Route>
        </MemoryRouter>
      </AnalyticsContext.Provider>,
    );

    await waitFor(() => getByText('assetA'));

    // Check if the loaded content is displayed
    expect(getByText('Jan 1, 1970, 12:16:40 AM')).toBeVisible();
    expect(getByText('Duration')).toBeVisible();
    expect(getByText('Partition Selection')).toBeVisible();
    expect(getByText('Status')).toBeVisible();
    expect(getByText('Asset name')).toBeVisible();
    expect(getByText('Partitions targeted')).toBeVisible();
    expect(getAllByText('Requested').length).toBe(1);
    expect(getByText('Completed')).toBeVisible();
    expect(getByText('Failed')).toBeVisible();

    // Check if the correct data is displayed
    expect(getByText('assetA')).toBeVisible();
    expect(getByText('3')).toBeVisible(); // numPartitionsTargeted
    expect(getByText('2')).toBeVisible(); // numPartitionsInProgress
    expect(getByText('1')).toBeVisible(); // numPartitionsMaterialized
    expect(getByText('0')).toBeVisible(); // numPartitionsFailed
  });
});

describe('PartitionSelection', () => {
  it('renders the targeted partitions when rootAssetTargetedPartitions is provided and length <= 3', () => {
    const {getByText} = render(
      <PartitionSelection numPartitions={3} rootAssetTargetedPartitions={['1', '2', '3']} />,
    );

    expect(getByText('1')).toBeInTheDocument();
    expect(getByText('2')).toBeInTheDocument();
    expect(getByText('3')).toBeInTheDocument();
  });

  it('renders the targeted partitions in a dialog when rootAssetTargetedPartitions is provided and length > 3', () => {
    const {getByText} = render(
      <PartitionSelection numPartitions={4} rootAssetTargetedPartitions={['1', '2', '3', '4']} />,
    );

    fireEvent.click(getByText('4 partitions'));

    expect(getByText('1')).toBeInTheDocument();
    expect(getByText('2')).toBeInTheDocument();
    expect(getByText('3')).toBeInTheDocument();
    expect(getByText('4')).toBeInTheDocument();
  });

  it('renders the single targeted range when rootAssetTargetedRanges is provided and length === 1', () => {
    const {getByText} = render(
      <PartitionSelection
        numPartitions={1}
        rootAssetTargetedRanges={[buildPartitionKeyRange({start: '1', end: '2'})]}
      />,
    );

    expect(getByText('1...2')).toBeInTheDocument();
  });

  it('renders the targeted ranges in a dialog when rootAssetTargetedRanges is provided and length > 1', () => {
    const {getByText} = render(
      <PartitionSelection
        numPartitions={2}
        rootAssetTargetedRanges={[
          buildPartitionKeyRange({start: '1', end: '2'}),
          buildPartitionKeyRange({start: '3', end: '4'}),
        ]}
      />,
    );

    fireEvent.click(getByText('2 partitions'));

    expect(getByText('1...2')).toBeInTheDocument();
    expect(getByText('3...4')).toBeInTheDocument();
  });

  it('renders the numPartitions in a ButtonLink when neither rootAssetTargetedPartitions nor rootAssetTargetedRanges are provided', () => {
    const {getByText} = render(<PartitionSelection numPartitions={2} />);

    expect(getByText('2 partitions')).toBeInTheDocument();
  });
});
