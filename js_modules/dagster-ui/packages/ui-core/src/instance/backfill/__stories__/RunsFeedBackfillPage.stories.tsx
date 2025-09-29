import {MockedProvider} from '@apollo/client/testing';
import {StoryFn} from '@storybook/nextjs';
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
  buildUnpartitionedAssetStatus,
} from '../../../graphql/types';
import {RunsFeedBackfillPage} from '../RunsFeedBackfillPage';
import {buildBackfillDetailsQuery} from '../__fixtures__/buildBackfillDetails';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Runs/Backfills',
  component: RunsFeedBackfillPage,
};

const Template: StoryFn = ({mocks}) => (
  <RecoilRoot>
    <AnalyticsContext.Provider value={{page: () => {}} as any}>
      <MemoryRouter initialEntries={['/runs/b/1']}>
        <MockedProvider mocks={mocks}>
          <Route path="/runs/b/:backfillId">
            <RunsFeedBackfillPage />
          </Route>
        </MockedProvider>
      </MemoryRouter>
    </AnalyticsContext.Provider>
  </RecoilRoot>
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

const assetAKey = buildAssetKey({path: ['assetA']});
const assetBKey = buildAssetKey({path: ['assetB']});

const CompletedResponse = buildBackfillDetailsQuery(
  '1',
  buildPartitionBackfill({
    id: '1',
    status: BulkActionStatus.COMPLETED,
    timestamp: Date.now() / 1000 - 10000,
    assetBackfillData: buildAssetBackfillData({
      assetBackfillStatuses: [
        buildUnpartitionedAssetStatus({
          assetKey: assetAKey,
          failed: false,
          materialized: false,
          inProgress: false,
        }),
        buildUnpartitionedAssetStatus({
          assetKey: assetBKey,
          failed: true,
          materialized: false,
          inProgress: false,
        }),
        buildUnpartitionedAssetStatus({
          assetKey: assetAKey,
          failed: false,
          materialized: true,
          inProgress: false,
        }),
        buildUnpartitionedAssetStatus({
          assetKey: assetBKey,
          failed: false,
          materialized: false,
          inProgress: true,
        }),
        buildAssetPartitionsStatusCounts({
          assetKey: assetAKey,
          numPartitionsMaterialized: 50,
          numPartitionsFailed: 50,
          numPartitionsTargeted: 100,
          numPartitionsInProgress: 0,
        }),
        buildAssetPartitionsStatusCounts({
          assetKey: assetBKey,
          numPartitionsMaterialized: 10,
          numPartitionsFailed: 90,
          numPartitionsTargeted: 100,
          numPartitionsInProgress: 0,
        }),
        buildAssetPartitionsStatusCounts({
          assetKey: assetAKey,
          numPartitionsMaterialized: 10,
          numPartitionsFailed: 90,
          numPartitionsTargeted: 100,
          numPartitionsInProgress: 0,
        }),
        buildAssetPartitionsStatusCounts({
          assetKey: assetBKey,
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
