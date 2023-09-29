import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {Box} from '@dagster-io/ui-components';
import React from 'react';

import {createAppCache} from '../../app/AppCache';
import {
  AssetFreshnessInfo,
  FreshnessPolicy,
  buildAssetFreshnessInfo,
  buildAssetKey,
  buildAssetNode,
  buildFreshnessPolicy,
  buildQuery,
} from '../../graphql/types';
import {OVERDUE_POPOVER_QUERY, OverdueTag} from '../OverdueTag';
import {OverduePopoverQuery, OverduePopoverQueryVariables} from '../types/OverdueTag.types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Assets/OverdueTag',
  component: OverdueTag,
};

const TEST_LAG_MINUTES = 4 * 60 + 30;
const TEST_TIME = Date.now();
const LAST_MATERIALIZATION_TIME = TEST_TIME - 4 * 60 * 1000;

// const mockLiveData = {
//   ...LiveDataForNodeMaterializedAndOverdue,
//   lastMaterialization: {
//     ...LiveDataForNodeMaterializedAndOverdue.lastMaterialization!,
//     timestamp: `${LAST_MATERIALIZATION_TIME}`,
//   },
// };

function buildOverduePopoverMock(
  policy: FreshnessPolicy,
  freshnessInfo: Partial<AssetFreshnessInfo>,
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
          freshnessInfo: buildAssetFreshnessInfo(freshnessInfo),
          assetMaterializationUsedData: hasUsedData
            ? [
                {
                  timestamp: `${TEST_TIME - TEST_LAG_MINUTES * 60 * 1000}`,
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
  const mockFreshnessPolicyCron = buildFreshnessPolicy({
    cronSchedule: '30 2 * * 1', // Monday at 2:30 Central
    cronScheduleTimezone: 'America/Chicago',
    maximumLagMinutes: 5,
    lastEvaluationTimestamp: `${TEST_TIME}`,
  });
  const freshnessInfo = {
    __typename: 'AssetFreshnessInfo' as const,
    currentMinutesLate: Math.max(0, TEST_LAG_MINUTES - mockFreshnessPolicyCron.maximumLagMinutes),
    currentLagMinutes: TEST_LAG_MINUTES,
  };

  return (
    <MockedProvider
      cache={createAppCache()}
      mocks={[buildOverduePopoverMock(mockFreshnessPolicyCron, freshnessInfo)]}
    >
      <Box style={{width: 400}} flex={{gap: 8, alignItems: 'center'}}>
        <OverdueTag assetKey={{path: ['inp8']}} policy={mockFreshnessPolicyCron} />
        Hover for details, times are relative to last cron tick (eg: earlier). Note: The relative
        materialization times in the modal are not mocked to align with the cron schedule tick.
      </Box>
    </MockedProvider>
  );
};

export const OverdueNoSchedule = () => {
  const mockFreshnessPolicy = buildFreshnessPolicy({
    cronSchedule: null,
    cronScheduleTimezone: null,
    maximumLagMinutes: 60,
    lastEvaluationTimestamp: `${TEST_TIME}`,
  });
  const freshnessInfo = {
    __typename: 'AssetFreshnessInfo' as const,
    currentMinutesLate: Math.max(0, TEST_LAG_MINUTES - mockFreshnessPolicy.maximumLagMinutes),
    currentLagMinutes: TEST_LAG_MINUTES,
  };

  return (
    <MockedProvider
      cache={createAppCache()}
      mocks={[buildOverduePopoverMock(mockFreshnessPolicy, freshnessInfo)]}
    >
      <Box style={{width: 400}} flex={{gap: 8, alignItems: 'center'}}>
        <OverdueTag assetKey={{path: ['inp8']}} policy={mockFreshnessPolicy} />
        {' Hover for details, times are relative to now (eg: "ago")'}
      </Box>
    </MockedProvider>
  );
};

export const OverdueNoUpstreams = () => {
  const mockFreshnessPolicy = buildFreshnessPolicy({
    cronSchedule: null,
    cronScheduleTimezone: null,
    maximumLagMinutes: 2,
    lastEvaluationTimestamp: `${TEST_TIME}`,
  });

  const currentLagMinutes = (TEST_TIME - LAST_MATERIALIZATION_TIME) / (60 * 1000);
  const freshnessInfo = {
    __typename: 'AssetFreshnessInfo' as const,
    currentMinutesLate: Math.max(0, currentLagMinutes - mockFreshnessPolicy.maximumLagMinutes),
    currentLagMinutes,
  };

  return (
    <MockedProvider
      cache={createAppCache()}
      mocks={[buildOverduePopoverMock(mockFreshnessPolicy, freshnessInfo, false)]}
    >
      <Box style={{width: 400}} flex={{gap: 8, alignItems: 'center'}}>
        <OverdueTag assetKey={{path: ['inp8']}} policy={mockFreshnessPolicy} />
        {' Hover for details. "derived from upstream data" omitted from description.'}
      </Box>
    </MockedProvider>
  );
};

export const NeverMaterialized = () => {
  const mockFreshnessPolicy = buildFreshnessPolicy({
    cronSchedule: null,
    cronScheduleTimezone: null,
    maximumLagMinutes: 24 * 60,
    lastEvaluationTimestamp: `${TEST_TIME}`,
  });
  // const freshnessInfo = {
  //   __typename: 'AssetFreshnessInfo' as const,
  //   currentMinutesLate: null,
  //   currentLagMinutes: null,
  // };

  return (
    <MockedProvider cache={createAppCache()} mocks={[]}>
      <OverdueTag assetKey={{path: ['inp8']}} policy={mockFreshnessPolicy} />
    </MockedProvider>
  );
};

export const Fresh = () => {
  const mockFreshnessPolicyMet = buildFreshnessPolicy({
    cronSchedule: null,
    cronScheduleTimezone: null,
    maximumLagMinutes: 24 * 60,
    lastEvaluationTimestamp: `${TEST_TIME}`,
  });
  const freshnessInfo = {
    __typename: 'AssetFreshnessInfo' as const,
    currentMinutesLate: 0,
    currentLagMinutes: TEST_LAG_MINUTES,
  };

  return (
    <MockedProvider
      cache={createAppCache()}
      mocks={[buildOverduePopoverMock(mockFreshnessPolicyMet, freshnessInfo)]}
    >
      <OverdueTag assetKey={{path: ['inp8']}} policy={mockFreshnessPolicyMet} />
    </MockedProvider>
  );
};

export const NoFreshnessInfo = () => {
  const mockFreshnessPolicy = buildFreshnessPolicy({
    cronSchedule: null,
    cronScheduleTimezone: null,
    maximumLagMinutes: 24 * 60,
    lastEvaluationTimestamp: `${TEST_TIME}`,
  });
  return (
    <MockedProvider cache={createAppCache()} mocks={[]}>
      <OverdueTag assetKey={{path: ['inp8']}} policy={mockFreshnessPolicy} />
    </MockedProvider>
  );
};
