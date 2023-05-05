import {MockedProvider} from '@apollo/client/testing';
import {Story, Meta} from '@storybook/react';
import React from 'react';
import {MemoryRouter, Route} from 'react-router-dom';

import {AnalyticsContext} from '../../../app/analytics';
import {
  BulkActionStatus,
  buildAssetBackfillData,
  buildAssetPartitionsStatusCounts,
  buildPartitionBackfill,
} from '../../../graphql/types';
import {BackfillPage} from '../BackfillPage';
import {buildBackfillDetailsQuery} from '../__fixtures__/buildBackfillDetails';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'BackfillPage',
  component: BackfillPage,
} as Meta;

const Template: Story = ({mocks}) => (
  <AnalyticsContext.Provider value={{page: () => {}} as any}>
    <MemoryRouter initialEntries={['/backfill/1']}>
      <MockedProvider mocks={mocks}>
        <Route path="/backfill/:backfillId">
          <BackfillPage />
        </Route>
      </MockedProvider>
    </MemoryRouter>
  </AnalyticsContext.Provider>
);

export const Completed = () => {
  return <Template mocks={[CompletedResponse]} />;
};

export const InProgress = () => {
  return <Template mocks={[InProgressResponse]} />;
};

export const Failed = () => {
  return <Template mocks={[FailedResponse]} />;
};

export const Canceled = () => {
  return <Template mocks={[CanceledResponse]} />;
};

const CompletedResponse = buildBackfillDetailsQuery(
  '1',
  buildPartitionBackfill({
    id: '1',
    status: BulkActionStatus.COMPLETED,
    timestamp: Date.now() / 1000 - 10000,
    assetBackfillData: buildAssetBackfillData({
      assetBackfillStatuses: [
        buildAssetPartitionsStatusCounts({
          numPartitionsMaterialized: 50,
          numPartitionsFailed: 50,
          numPartitionsTargeted: 100,
          numPartitionsInProgress: 0,
        }),
        buildAssetPartitionsStatusCounts({
          numPartitionsMaterialized: 10,
          numPartitionsFailed: 90,
          numPartitionsTargeted: 100,
          numPartitionsInProgress: 0,
        }),
        buildAssetPartitionsStatusCounts({
          numPartitionsMaterialized: 10,
          numPartitionsFailed: 90,
          numPartitionsTargeted: 100,
          numPartitionsInProgress: 0,
        }),
        buildAssetPartitionsStatusCounts({
          numPartitionsMaterialized: 10,
          numPartitionsFailed: 90,
          numPartitionsTargeted: 100,
          numPartitionsInProgress: 0,
        }),
      ],
    }),
  }),
);

const InProgressResponse = buildBackfillDetailsQuery(
  '1',
  buildPartitionBackfill({
    id: '1',
    status: BulkActionStatus.REQUESTED,
    timestamp: Date.now() / 1000 - 10000,
    endTimestamp: Date.now() / 1000 - 10,
    assetBackfillData: buildAssetBackfillData({
      assetBackfillStatuses: [
        buildAssetPartitionsStatusCounts({
          numPartitionsMaterialized: 25,
          numPartitionsFailed: 25,
          numPartitionsTargeted: 100,
          numPartitionsInProgress: 25,
        }),
        buildAssetPartitionsStatusCounts({
          numPartitionsMaterialized: 25,
          numPartitionsFailed: 25,
          numPartitionsTargeted: 100,
          numPartitionsInProgress: 25,
        }),
        buildAssetPartitionsStatusCounts({
          numPartitionsMaterialized: 25,
          numPartitionsFailed: 25,
          numPartitionsTargeted: 100,
          numPartitionsInProgress: 25,
        }),
        buildAssetPartitionsStatusCounts({
          numPartitionsMaterialized: 25,
          numPartitionsFailed: 25,
          numPartitionsTargeted: 100,
          numPartitionsInProgress: 25,
        }),
      ],
    }),
  }),
);

const CanceledResponse = buildBackfillDetailsQuery(
  '1',
  buildPartitionBackfill({
    id: '1',
    status: BulkActionStatus.CANCELED,
    timestamp: Date.now() / 1000 - 10000,
    endTimestamp: Date.now() / 1000 - 10,
    assetBackfillData: buildAssetBackfillData({
      assetBackfillStatuses: [
        buildAssetPartitionsStatusCounts({
          numPartitionsMaterialized: 25,
          numPartitionsFailed: 25,
          numPartitionsTargeted: 100,
          numPartitionsInProgress: 25,
        }),
      ],
    }),
  }),
);

const FailedResponse = buildBackfillDetailsQuery(
  '1',
  buildPartitionBackfill({
    id: '1',
    status: BulkActionStatus.FAILED,
    timestamp: Date.now() / 1000 - 10000,
    endTimestamp: Date.now() / 1000 - 10,
    assetBackfillData: buildAssetBackfillData({
      assetBackfillStatuses: [
        buildAssetPartitionsStatusCounts({
          numPartitionsMaterialized: 25,
          numPartitionsFailed: 25,
          numPartitionsTargeted: 100,
          numPartitionsInProgress: 25,
        }),
      ],
    }),
  }),
);
