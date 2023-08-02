import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {Box} from '@dagster-io/ui-components';
import React from 'react';

import {createAppCache} from '../../app/AppCache';
import {
  LiveDataForNodeMaterialized,
  LiveDataForNodeMaterializedAndOverdue,
  LiveDataForNodeMaterializedAndFresh,
} from '../../asset-graph/__fixtures__/AssetNode.fixtures';
import {
  FreshnessPolicy,
  buildAssetKey,
  buildAssetNode,
  buildFreshnessPolicy,
  buildQuery,
} from '../../graphql/types';
import {OVERDUE_POPOVER_QUERY, OverdueTag} from '../OverdueTag';
import {OverduePopoverQuery, OverduePopoverQueryVariables} from '../types/OverdueTag.types';

// eslint-disable-next-line import/no-default-export
export default {component: OverdueTag};

const TEST_TIME = 1689561000000;
const LAST_MATERIALIZATION_TIME = TEST_TIME - 4 * 60 * 1000;

const mockLiveData = {
  ...LiveDataForNodeMaterializedAndOverdue,
  lastMaterialization: {
    ...LiveDataForNodeMaterializedAndOverdue.lastMaterialization!,
    timestamp: `${LAST_MATERIALIZATION_TIME}`,
  },
};

const mockFreshnessPolicyCron = buildFreshnessPolicy({
  cronSchedule: '30 2 * * 1', // Monday at 2:30 Central
  cronScheduleTimezone: 'America/Chicago',
  maximumLagMinutes: 5,
  lastEvaluationTimestamp: `${TEST_TIME}`,
});

const mockFreshnessPolicy = buildFreshnessPolicy({
  cronSchedule: null,
  cronScheduleTimezone: null,
  maximumLagMinutes: 24 * 60,
  lastEvaluationTimestamp: `${TEST_TIME}`,
});

function buildOverduePopoverMock(
  policy: FreshnessPolicy,
  hasUsedData = true,
): MockedResponse<OverduePopoverQuery, OverduePopoverQueryVariables> {
  return {
    request: {
      query: OVERDUE_POPOVER_QUERY,
      variables: {
        assetKey: {path: ['inp8']},
        timestamp: `${LAST_MATERIALIZATION_TIME}`,
      },
    },
    result: {
      data: buildQuery({
        assetNodeOrError: buildAssetNode({
          id: 'test.py.repo.["inp8"]',
          freshnessPolicy: policy,
          assetMaterializationUsedData: hasUsedData
            ? [
                {
                  timestamp: `${TEST_TIME - 24 * 60 * 60 * 1000}`,
                  assetKey: buildAssetKey({
                    path: ['inp1'],
                  }),
                  downstreamAssetKey: buildAssetKey({
                    path: ['inp8'],
                  }),
                  __typename: 'MaterializationUpstreamDataVersion',
                },
                {
                  timestamp: `${TEST_TIME - 3 * 60 * 1000}`,
                  assetKey: buildAssetKey({
                    path: ['inp2'],
                  }),
                  downstreamAssetKey: buildAssetKey({
                    path: ['inp8'],
                  }),
                  __typename: 'MaterializationUpstreamDataVersion',
                },
              ]
            : [],
        }),
      }),
    },
  };
}

export const OverdueCronSchedule = () => {
  return (
    <MockedProvider
      cache={createAppCache()}
      mocks={[buildOverduePopoverMock(mockFreshnessPolicyCron)]}
    >
      <Box style={{width: 400}} flex={{gap: 8, alignItems: 'center'}}>
        <OverdueTag
          assetKey={{path: ['inp8']}}
          liveData={mockLiveData}
          policy={mockFreshnessPolicyCron}
        />
        {' Hover for details, times are relative to last cron tick (eg: "earlier")'}
      </Box>
    </MockedProvider>
  );
};

export const OverdueNoSchedule = () => {
  return (
    <MockedProvider cache={createAppCache()} mocks={[buildOverduePopoverMock(mockFreshnessPolicy)]}>
      <Box style={{width: 400}} flex={{gap: 8, alignItems: 'center'}}>
        <OverdueTag
          assetKey={{path: ['inp8']}}
          liveData={mockLiveData}
          policy={mockFreshnessPolicy}
        />
        {' Hover for details, times are relative to now (eg: "ago")'}
      </Box>
    </MockedProvider>
  );
};

export const OverdueNoUpstreams = () => {
  return (
    <MockedProvider
      cache={createAppCache()}
      mocks={[buildOverduePopoverMock(mockFreshnessPolicy, false)]}
    >
      <Box style={{width: 400}} flex={{gap: 8, alignItems: 'center'}}>
        <OverdueTag
          assetKey={{path: ['inp8']}}
          liveData={mockLiveData}
          policy={mockFreshnessPolicy}
        />
        {' Hover for details. "derived from upstream data" omitted from description.'}
      </Box>
    </MockedProvider>
  );
};

export const NeverMaterialized = () => {
  return (
    <MockedProvider cache={createAppCache()} mocks={[]}>
      <OverdueTag
        assetKey={{path: ['inp8']}}
        policy={mockFreshnessPolicy}
        liveData={{
          ...mockLiveData,
          freshnessInfo: {__typename: 'AssetFreshnessInfo', currentMinutesLate: null},
        }}
      />
    </MockedProvider>
  );
};

export const Fresh = () => {
  return (
    <MockedProvider cache={createAppCache()} mocks={[]}>
      <OverdueTag
        assetKey={{path: ['inp8']}}
        policy={mockFreshnessPolicy}
        liveData={LiveDataForNodeMaterializedAndFresh}
      />
    </MockedProvider>
  );
};

export const NotLate = () => {
  return (
    <MockedProvider cache={createAppCache()} mocks={[]}>
      <OverdueTag
        assetKey={{path: ['inp8']}}
        liveData={LiveDataForNodeMaterialized}
        policy={mockFreshnessPolicy}
      />
    </MockedProvider>
  );
};
