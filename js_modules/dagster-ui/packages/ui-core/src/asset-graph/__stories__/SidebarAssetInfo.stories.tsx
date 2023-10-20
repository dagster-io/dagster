import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {Box} from '@dagster-io/ui-components';
import React from 'react';

import {createAppCache} from '../../app/AppCache';
import {buildPartitionHealthMock} from '../../assets/__fixtures__/PartitionHealthQuery.fixtures';
import {AssetEventsQuery} from '../../assets/types/useRecentAssetEvents.types';
import {ASSET_EVENTS_QUERY} from '../../assets/useRecentAssetEvents';
import {
  AssetNode,
  AutoMaterializeDecisionType,
  AutoMaterializePolicyType,
  RunStatus,
  buildAssetNode,
  buildAutoMaterializePolicy,
  buildAutoMaterializeRule,
  buildFreshnessPolicy,
} from '../../graphql/types';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext';
import {SIDEBAR_ASSET_QUERY, SidebarAssetInfo} from '../SidebarAssetInfo';
import {GraphNode} from '../Utils';
import {SidebarAssetQuery} from '../types/SidebarAssetInfo.types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Asset Graph/SidebarAssetInfo',
  component: SidebarAssetInfo,
};

const MockRepo = {
  __typename: 'Repository',
  id: 'test.py.repo',
  name: 'test.py',
  location: {__typename: 'RepositoryLocation', id: 'repo', name: 'repo'},
} as const;

const MockAssetKey = {__typename: 'AssetKey' as const, path: ['asset1']};

const buildGraphNodeMock = (definitionOverrides: Partial<AssetNode>): GraphNode => ({
  id: 'test.py.repo.["asset1"]',
  assetKey: MockAssetKey,
  definition: buildAssetNode({
    id: 'test.py.repo.["asset1"]',
    assetKey: MockAssetKey,
    jobNames: ['__ASSET_JOB_1'],
    opNames: ['asset1'],
    groupName: null,
    graphName: null,
    isPartitioned: false,
    isObservable: false,
    isSource: false,
    ...definitionOverrides,
  }),
});

const buildSidebarQueryMock = (
  overrides: Partial<SidebarAssetQuery['assetNodeOrError']> = {},
): MockedResponse<SidebarAssetQuery> => ({
  request: {
    query: SIDEBAR_ASSET_QUERY,
    variables: {
      assetKey: {
        path: ['asset1'],
      },
    },
  },
  result: {
    data: {
      __typename: 'Query',
      assetNodeOrError: {
        __typename: 'AssetNode',
        id: 'test.py.repo.["asset1"]',
        description: null,
        configField: null,
        metadataEntries: [],
        assetChecks: [],
        jobNames: ['test_job'],
        autoMaterializePolicy: null,
        freshnessPolicy: null,
        partitionDefinition: null,
        assetKey: {
          path: ['asset1'],
          __typename: 'AssetKey',
        },
        op: {
          name: 'asset1',
          description: null,
          metadata: [
            {
              key: 'compute_kind',
              value: 'pandas',
              __typename: 'MetadataItemDefinition',
            },
            {
              key: 'kind',
              value: 'pandas',
              __typename: 'MetadataItemDefinition',
            },
          ],
          __typename: 'SolidDefinition',
        },
        opVersion: null,
        repository: MockRepo,
        requiredResources: [
          {
            __typename: 'ResourceRequirement',
            resourceKey: 'foobar',
          },
          {
            __typename: 'ResourceRequirement',
            resourceKey: 'barbaz',
          },
          {
            __typename: 'ResourceRequirement',
            resourceKey: 'FOO_BAR',
          },
          {
            __typename: 'ResourceRequirement',
            resourceKey: 'just_another_resource',
          },
        ],
        type: {
          key: 'Any',
          name: 'Any',
          displayName: 'Any',
          description: null,
          isNullable: false,
          isList: false,
          isBuiltin: true,
          isNothing: false,
          metadataEntries: [],
          inputSchemaType: {
            __typename: 'CompositeConfigType',
            key: 'Selector.f2fe6dfdc60a1947a8f8e7cd377a012b47065bc4',
            description: null,
            isSelector: true,
            typeParamKeys: [],
            fields: [],
            recursiveConfigTypes: [],
          },
          outputSchemaType: null,
          __typename: 'RegularDagsterType',
          innerTypes: [],
        },
        ...overrides,
      },
    },
  },
});

const buildEventsMock = ({reported}: {reported: boolean}): MockedResponse<AssetEventsQuery> => ({
  request: {
    query: ASSET_EVENTS_QUERY,
    variables: {
      assetKey: {path: ['asset1']},
      before: undefined,
      limit: 100,
    },
  },
  result: {
    data: {
      __typename: 'Query',
      assetOrError: {
        __typename: 'Asset',
        key: MockAssetKey,
        id: '["asset1"]',
        definition: {
          __typename: 'AssetNode',
          id: 'test.py.repo.["asset1"]',
          partitionKeys: [],
        },
        assetMaterializations: [
          {
            __typename: 'MaterializationEvent',
            description: '1234',
            metadataEntries: [],
            partition: null,
            timestamp: '1234567865400',
            assetLineage: [],
            label: null,
            stepKey: 'op',
            tags: [],
            runId: reported ? '' : '12345',
            runOrError: reported
              ? {__typename: 'RunNotFoundError'}
              : {
                  __typename: 'Run',
                  pipelineName: '__ASSET_JOB_1',
                  mode: 'default',
                  pipelineSnapshotId: null,
                  id: '12345',
                  status: RunStatus.SUCCESS,
                  repositoryOrigin: {
                    __typename: 'RepositoryOrigin',
                    id: 'test.py',
                    repositoryLocationName: 'repo',
                    repositoryName: 'test.py',
                  },
                },
          },
        ],
        assetObservations: [
          {
            __typename: 'ObservationEvent',
            description: '1234',
            runId: '12345',
            metadataEntries: [],
            partition: null,
            timestamp: '1234567865400',
            label: null,
            stepKey: 'op',
            tags: [],
            runOrError: {
              __typename: 'Run',
              pipelineName: '__ASSET_JOB_1',
              mode: 'default',
              pipelineSnapshotId: null,
              id: '12345',
              status: RunStatus.SUCCESS,
              repositoryOrigin: {
                __typename: 'RepositoryOrigin',
                id: 'test.py',
                repositoryLocationName: 'repo',
                repositoryName: 'test.py',
              },
            },
          },
        ],
      },
    },
  },
});

const TestContainer: React.FC<{
  mocks?: MockedResponse<Record<string, any>>[];
  children: React.ReactNode;
}> = ({children, mocks}) => (
  <MockedProvider
    cache={createAppCache()}
    mocks={
      mocks || [
        buildEventsMock({reported: false}),
        buildPartitionHealthMock(MockAssetKey.path[0]!),
        buildSidebarQueryMock(),
      ]
    }
  >
    <WorkspaceProvider>
      <Box style={{width: 400}}>{children}</Box>
    </WorkspaceProvider>
  </MockedProvider>
);

export const AssetWithMaterialization = () => {
  return (
    <TestContainer>
      <SidebarAssetInfo graphNode={buildGraphNodeMock({})} />
    </TestContainer>
  );
};

export const AssetWithReportedMaterialization = () => {
  return (
    <TestContainer
      mocks={[
        buildEventsMock({reported: true}),
        buildPartitionHealthMock(MockAssetKey.path[0]!),
        buildSidebarQueryMock(),
      ]}
    >
      <SidebarAssetInfo graphNode={buildGraphNodeMock({})} />
    </TestContainer>
  );
};

export const AssetWithPolicies = () => {
  return (
    <TestContainer
      mocks={[
        buildEventsMock({reported: false}),
        buildPartitionHealthMock(MockAssetKey.path[0]!),
        buildSidebarQueryMock({
          autoMaterializePolicy: buildAutoMaterializePolicy({
            policyType: AutoMaterializePolicyType.EAGER,
            rules: [
              buildAutoMaterializeRule({
                decisionType: AutoMaterializeDecisionType.MATERIALIZE,
                description: 'Rule 1',
              }),
              buildAutoMaterializeRule({
                decisionType: AutoMaterializeDecisionType.SKIP,
                description: 'Skip Rule 1',
              }),
            ],
          }),
          freshnessPolicy: buildFreshnessPolicy({
            maximumLagMinutes: 60,
            cronSchedule: '* 1 1 1 1',
          }),
        }),
      ]}
    >
      <SidebarAssetInfo graphNode={buildGraphNodeMock({})} />
    </TestContainer>
  );
};

export const AssetWithGraphName = () => {
  return (
    <TestContainer>
      <SidebarAssetInfo graphNode={buildGraphNodeMock({graphName: 'op_graph'})} />
    </TestContainer>
  );
};

export const AssetWithAssetChecks = () => {
  return (
    <TestContainer>
      <SidebarAssetInfo graphNode={buildGraphNodeMock({})} />
    </TestContainer>
  );
};

export const AssetWithDifferentOpName = () => {
  return (
    <TestContainer>
      <SidebarAssetInfo graphNode={buildGraphNodeMock({opNames: ['not_asset_name']})} />
    </TestContainer>
  );
};

export const ObservableSourceAsset = () => {
  return (
    <TestContainer>
      <SidebarAssetInfo graphNode={buildGraphNodeMock({isObservable: true, isSource: true})} />
    </TestContainer>
  );
};
