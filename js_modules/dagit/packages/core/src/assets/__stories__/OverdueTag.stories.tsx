import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {Box} from '@dagster-io/ui';
import React from 'react';

import {createAppCache} from '../../app/AppCache';
import {
  LiveDataForNodeMaterialized,
  LiveDataForNodeMaterializedAndOverdue,
  LiveDataForNodeNeverMaterialized,
  LiveDataForNodeMaterializedAndFresh,
} from '../../asset-graph/__fixtures__/AssetNode.fixtures';
import {buildAssetKey, buildAssetNode, buildFreshnessPolicy, buildQuery} from '../../graphql/types';
import {OVERDUE_POPOVER_QUERY, OverdueTag} from '../OverdueTag';
import {OverduePopoverQuery, OverduePopoverQueryVariables} from '../types/OverdueTag.types';

// eslint-disable-next-line import/no-default-export
export default {component: OverdueTag};

const mockFreshnessPolicy = buildFreshnessPolicy({
  cronSchedule: '30 2 * * *',
  cronScheduleTimezone: null,
  maximumLagMinutes: 2,
});

function buildOverduePopoverMock(): MockedResponse<
  OverduePopoverQuery,
  OverduePopoverQueryVariables
> {
  return {
    request: {
      query: OVERDUE_POPOVER_QUERY,
      variables: {
        assetKey: {path: ['inp8']},
        timestamp: LiveDataForNodeMaterializedAndOverdue.lastMaterialization!.timestamp,
      },
    },
    result: {
      data: buildQuery({
        assetNodeOrError: buildAssetNode({
          id: 'test.py.repo.["inp8"]',
          freshnessPolicy: mockFreshnessPolicy,
          assetMaterializationUsedData: [
            {
              timestamp: '1684596878856',
              assetKey: buildAssetKey({
                path: ['inp1'],
              }),
              downstreamAssetKey: buildAssetKey({
                path: ['inp8'],
              }),
              __typename: 'MaterializationUpstreamDataVersion',
            },
            {
              timestamp: '1686943124049',
              assetKey: buildAssetKey({
                path: ['inp2'],
              }),
              downstreamAssetKey: buildAssetKey({
                path: ['inp8'],
              }),
              __typename: 'MaterializationUpstreamDataVersion',
            },
          ],
          __typename: 'AssetNode',
        }),
      }),
    },
  };
}

const TestContainer: React.FC<{
  children: React.ReactNode;
}> = ({children}) => (
  <MockedProvider cache={createAppCache()} mocks={[buildOverduePopoverMock()]}>
    <Box style={{width: 400}}>{children}</Box>
  </MockedProvider>
);

export const Basic = () => {
  return (
    <TestContainer>
      <OverdueTag
        assetKey={{path: ['inp8']}}
        liveData={LiveDataForNodeMaterializedAndOverdue}
        policy={mockFreshnessPolicy}
      />{' '}
      (Hover for details)
    </TestContainer>
  );
};

export const NeverMaterialized = () => {
  return (
    <TestContainer>
      <OverdueTag
        assetKey={{path: ['inp8']}}
        policy={mockFreshnessPolicy}
        liveData={{
          ...LiveDataForNodeNeverMaterialized,
          freshnessInfo: {__typename: 'AssetFreshnessInfo', currentMinutesLate: null},
        }}
      />
    </TestContainer>
  );
};

export const Fresh = () => {
  return (
    <TestContainer>
      <OverdueTag
        assetKey={{path: ['inp8']}}
        policy={mockFreshnessPolicy}
        liveData={LiveDataForNodeMaterializedAndFresh}
      />
    </TestContainer>
  );
};

export const NotLate = () => {
  return (
    <TestContainer>
      <OverdueTag
        assetKey={{path: ['inp8']}}
        liveData={LiveDataForNodeMaterialized}
        policy={mockFreshnessPolicy}
      />
    </TestContainer>
  );
};
