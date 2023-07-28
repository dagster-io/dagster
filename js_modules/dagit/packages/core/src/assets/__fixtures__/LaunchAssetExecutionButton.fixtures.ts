import {MockedResponse} from '@apollo/client/testing';

import {tokenForAssetKey} from '../../asset-graph/Utils';
import {AssetNodeForGraphQueryFragment} from '../../asset-graph/types/useAssetGraphData.types';
import {
  AssetKeyInput,
  LaunchBackfillParams,
  PartitionDefinitionType,
  PartitionRangeStatus,
  buildDaemonHealth,
  buildDaemonStatus,
  buildDimensionDefinitionType,
  buildInstance,
  buildRunLauncher,
} from '../../graphql/types';
import {LAUNCH_PARTITION_BACKFILL_MUTATION} from '../../instance/BackfillUtils';
import {LaunchPartitionBackfillMutation} from '../../instance/types/BackfillUtils.types';
import {CONFIG_PARTITION_SELECTION_QUERY} from '../../launchpad/ConfigEditorConfigPicker';
import {ConfigPartitionSelectionQuery} from '../../launchpad/types/ConfigEditorConfigPicker.types';
import {LAUNCH_PIPELINE_EXECUTION_MUTATION} from '../../runs/RunUtils';
import {
  LaunchPipelineExecutionMutation,
  LaunchPipelineExecutionMutationVariables,
} from '../../runs/types/RunUtils.types';
import {LAUNCH_ASSET_WARNINGS_QUERY} from '../LaunchAssetChoosePartitionsDialog';
import {
  LAUNCH_ASSET_CHECK_UPSTREAM_QUERY,
  LAUNCH_ASSET_LOADER_QUERY,
  LAUNCH_ASSET_LOADER_RESOURCE_QUERY,
} from '../LaunchAssetExecutionButton';
import {LaunchAssetWarningsQuery} from '../types/LaunchAssetChoosePartitionsDialog.types';
import {
  LaunchAssetCheckUpstreamQuery,
  LaunchAssetLoaderQuery,
  LaunchAssetLoaderResourceQuery,
} from '../types/LaunchAssetExecutionButton.types';
import {PartitionHealthQuery} from '../types/usePartitionHealthData.types';
import {PARTITION_HEALTH_QUERY} from '../usePartitionHealthData';

import {generateDailyTimePartitions} from './PartitionHealthSummary.fixtures';

export const UNPARTITIONED_ASSET: AssetNodeForGraphQueryFragment = {
  __typename: 'AssetNode',
  id: 'test.py.repo.["unpartitioned_asset"]',
  groupName: 'mapped',
  hasMaterializePermission: true,
  repository: {
    __typename: 'Repository',
    id: 'c22d9677b8089be89b1e014b9de34284962f83a7',
    name: 'repo',
    location: {
      __typename: 'RepositoryLocation',
      id: 'test.py',
      name: 'test.py',
    },
  },
  dependencyKeys: [],
  dependedByKeys: [],
  graphName: null,
  jobNames: ['__ASSET_JOB_7', 'my_asset_job'],
  opNames: ['unpartitioned_asset'],
  opVersion: null,
  description: null,
  computeKind: null,
  isPartitioned: false,
  isObservable: false,
  isSource: false,
  assetKey: {
    __typename: 'AssetKey',
    path: ['unpartitioned_asset'],
  },
};

export const UNPARTITIONED_ASSET_OTHER_REPO: AssetNodeForGraphQueryFragment = {
  ...UNPARTITIONED_ASSET,
  id: 'test.py.repo.["unpartitioned_asset_other_repo"]',
  opNames: ['unpartitioned_asset_other_repo'],
  assetKey: {
    __typename: 'AssetKey',
    path: ['unpartitioned_asset_other_repo'],
  },
  repository: {
    __typename: 'Repository',
    id: '000000000000000000000000000000000000000',
    name: 'other-repo',
    location: {
      __typename: 'RepositoryLocation',
      id: 'other-location.py',
      name: 'other-location.py',
    },
  },
};

export const UNPARTITIONED_ASSET_WITH_REQUIRED_CONFIG: AssetNodeForGraphQueryFragment = {
  ...UNPARTITIONED_ASSET,
  id: 'test.py.repo.["unpartitioned_asset_with_required_config"]',
  opNames: ['unpartitioned_asset_with_required_config'],
  assetKey: {
    __typename: 'AssetKey',
    path: ['unpartitioned_asset_with_required_config'],
  },
};

export const ASSET_DAILY_PARTITION_KEYS = generateDailyTimePartitions(
  new Date('2020-01-01'),
  new Date('2023-02-22'),
);

export const ASSET_DAILY: AssetNodeForGraphQueryFragment = {
  __typename: 'AssetNode',
  id: 'test.py.repo.["asset_daily"]',
  groupName: 'mapped',
  hasMaterializePermission: true,
  repository: {
    __typename: 'Repository',
    id: 'c22d9677b8089be89b1e014b9de34284962f83a7',
    name: 'repo',
    location: {
      __typename: 'RepositoryLocation',
      id: 'test.py',
      name: 'test.py',
    },
  },
  dependencyKeys: [],
  dependedByKeys: [
    {
      __typename: 'AssetKey',
      path: ['asset_weekly'],
    },
  ],
  graphName: null,
  jobNames: ['__ASSET_JOB_7', 'my_asset_job'],
  opNames: ['asset_daily'],
  opVersion: null,
  description: null,
  computeKind: null,
  isPartitioned: true,
  isObservable: false,
  isSource: false,
  assetKey: {
    __typename: 'AssetKey',
    path: ['asset_daily'],
  },
};

export const ASSET_WEEKLY: AssetNodeForGraphQueryFragment = {
  __typename: 'AssetNode',
  id: 'test.py.repo.["asset_weekly"]',
  groupName: 'mapped',
  hasMaterializePermission: true,
  repository: {
    __typename: 'Repository',
    id: 'c22d9677b8089be89b1e014b9de34284962f83a7',
    name: 'repo',
    location: {
      __typename: 'RepositoryLocation',
      id: 'test.py',
      name: 'test.py',
    },
  },
  dependencyKeys: [
    {
      __typename: 'AssetKey',
      path: ['asset_daily'],
    },
  ],
  dependedByKeys: [],
  graphName: null,
  jobNames: ['__ASSET_JOB_8'],
  opNames: ['asset_weekly'],
  opVersion: null,
  description: null,
  computeKind: null,
  isPartitioned: true,
  isObservable: false,
  isSource: false,
  assetKey: {
    __typename: 'AssetKey',
    path: ['asset_weekly'],
  },
};

export const ASSET_WEEKLY_ROOT: AssetNodeForGraphQueryFragment = {
  ...ASSET_WEEKLY,
  id: 'test.py.repo.["asset_weekly_root"]',
  dependencyKeys: [],
  assetKey: {
    __typename: 'AssetKey',
    path: ['asset_weekly_root'],
  },
};

export const buildLaunchAssetWarningsMock = (
  upstreamAssetKeys: AssetKeyInput[],
): MockedResponse<LaunchAssetWarningsQuery> => ({
  request: {
    query: LAUNCH_ASSET_WARNINGS_QUERY,
    variables: {upstreamAssetKeys: upstreamAssetKeys.map((a) => ({path: a.path}))},
  },
  result: {
    data: {
      __typename: 'Query',
      assetNodes: [],
      instance: buildInstance({
        daemonHealth: buildDaemonHealth({
          id: 'daemonHealth',
          daemonStatus: buildDaemonStatus({
            id: 'BACKFILL',
            healthy: false,
          }),
        }),
        runQueuingSupported: false,
        runLauncher: buildRunLauncher({name: 'DefaultRunLauncher'}),
      }),
    },
  },
});

export const PartitionHealthAssetDailyMock: MockedResponse<PartitionHealthQuery> = {
  request: {
    query: PARTITION_HEALTH_QUERY,
    variables: {
      assetKey: {
        path: ['asset_daily'],
      },
    },
  },
  result: {
    data: {
      __typename: 'Query',
      assetNodeOrError: {
        id: 'test.py.repo.["asset_daily"]',
        partitionKeysByDimension: [
          {
            name: 'default',
            __typename: 'DimensionPartitionKeys',
            partitionKeys: ASSET_DAILY_PARTITION_KEYS,
            type: PartitionDefinitionType.TIME_WINDOW,
          },
        ],
        assetPartitionStatuses: {
          ranges: [
            {
              status: PartitionRangeStatus.MATERIALIZED,
              startTime: 1662940800.0,
              endTime: 1663027200.0,
              startKey: '2022-09-12',
              endKey: '2022-09-12',
              __typename: 'TimePartitionRangeStatus',
            },
            {
              status: PartitionRangeStatus.MATERIALIZED,
              startTime: 1663027200.0,
              endTime: 1667088000.0,
              startKey: '2022-09-13',
              endKey: '2022-10-29',
              __typename: 'TimePartitionRangeStatus',
            },
            {
              status: PartitionRangeStatus.MATERIALIZED,
              startTime: 1668816000.0,
              endTime: 1670803200.0,
              startKey: '2022-11-19',
              endKey: '2022-12-11',
              __typename: 'TimePartitionRangeStatus',
            },
            {
              status: PartitionRangeStatus.MATERIALIZED,
              startTime: 1671494400.0,
              endTime: 1674086400.0,
              startKey: '2022-12-20',
              endKey: '2023-01-18',
              __typename: 'TimePartitionRangeStatus',
            },
            {
              status: PartitionRangeStatus.MATERIALIZED,
              startTime: 1676851200.0,
              endTime: 1676937600.0,
              startKey: '2023-02-20',
              endKey: '2023-02-20',
              __typename: 'TimePartitionRangeStatus',
            },
          ],
          __typename: 'TimePartitionStatuses',
        },
        __typename: 'AssetNode',
      },
    },
  },
};

export const PartitionHealthAssetWeeklyMock: MockedResponse<PartitionHealthQuery> = {
  request: {
    query: PARTITION_HEALTH_QUERY,
    variables: {
      assetKey: {
        path: ['asset_weekly'],
      },
    },
  },
  result: {
    data: {
      __typename: 'Query',
      assetNodeOrError: {
        id: 'test.py.repo.["asset_weekly"]',
        partitionKeysByDimension: [
          {
            name: 'default',
            __typename: 'DimensionPartitionKeys',
            type: PartitionDefinitionType.TIME_WINDOW,
            partitionKeys: generateDailyTimePartitions(
              new Date('2020-01-01'),
              new Date('2023-02-22'),
              7,
            ),
          },
        ],
        assetPartitionStatuses: {
          ranges: [],
          __typename: 'TimePartitionStatuses',
        },
        __typename: 'AssetNode',
      },
    },
  },
};

export const PartitionHealthAssetWeeklyRootMock: MockedResponse<PartitionHealthQuery> = {
  request: {
    query: PARTITION_HEALTH_QUERY,
    variables: {
      assetKey: {
        path: ['asset_weekly_root'],
      },
    },
  },
  result: {
    data: {
      __typename: 'Query',
      assetNodeOrError: {
        id: 'test.py.repo.["asset_weekly_root"]',
        partitionKeysByDimension: [
          {
            name: 'default',
            __typename: 'DimensionPartitionKeys',
            type: PartitionDefinitionType.TIME_WINDOW,
            partitionKeys: generateDailyTimePartitions(
              new Date('2020-01-01'),
              new Date('2023-02-22'),
              7,
            ),
          },
        ],
        assetPartitionStatuses: {
          ranges: [],
          __typename: 'TimePartitionStatuses',
        },
        __typename: 'AssetNode',
      },
    },
  },
};

export const LaunchAssetLoaderResourceJob7Mock: MockedResponse<LaunchAssetLoaderResourceQuery> = {
  request: {
    query: LAUNCH_ASSET_LOADER_RESOURCE_QUERY,
    variables: {
      pipelineName: '__ASSET_JOB_7',
      repositoryLocationName: 'test.py',
      repositoryName: 'repo',
    },
  },
  result: {
    data: {
      __typename: 'Query',
      partitionSetsOrError: {
        results: [
          {
            id: '5b10aae97b738c48a4262b1eca530f89b13e9afc',
            name: '__ASSET_JOB_7_partition_set',
            __typename: 'PartitionSet',
          },
        ],
        __typename: 'PartitionSets',
      },
      pipelineOrError: {
        id: '8e2d3f9597c4a45bb52fe9ab5656419f4329d4fb',
        modes: [
          {
            id: 'da3055161c528f4c839339deb4a362ec1be4f079-default',
            resources: [
              {
                name: 'io_manager',
                description:
                  'Built-in filesystem IO manager that stores and retrieves values using pickling.',
                configField: {
                  name: 'config',
                  isRequired: false,
                  configType: {
                    __typename: 'CompositeConfigType',
                    key: 'Shape.18b2faaf1efd505374f7f25fcb61ed59bd5be851',
                    description: null,
                    isSelector: false,
                    typeParamKeys: [],
                    fields: [
                      {
                        name: 'base_dir',
                        description: null,
                        isRequired: false,
                        configTypeKey: 'StringSourceType',
                        defaultValueAsJson: null,
                        __typename: 'ConfigTypeField',
                      },
                    ],
                    recursiveConfigTypes: [
                      {
                        __typename: 'CompositeConfigType',
                        key: 'Selector.2571019f1a5201853d11032145ac3e534067f214',
                        description: null,
                        isSelector: true,
                        typeParamKeys: [],
                        fields: [
                          {
                            name: 'env',
                            description: null,
                            isRequired: true,
                            configTypeKey: 'String',
                            defaultValueAsJson: null,
                            __typename: 'ConfigTypeField',
                          },
                        ],
                      },
                      {
                        __typename: 'RegularConfigType',
                        givenName: 'String',
                        key: 'String',
                        description: '',
                        isSelector: false,
                        typeParamKeys: [],
                      },
                      {
                        __typename: 'ScalarUnionConfigType',
                        key: 'StringSourceType',
                        description: null,
                        isSelector: false,
                        typeParamKeys: [
                          'String',
                          'Selector.2571019f1a5201853d11032145ac3e534067f214',
                        ],
                        scalarTypeKey: 'String',
                        nonScalarTypeKey: 'Selector.2571019f1a5201853d11032145ac3e534067f214',
                      },
                    ],
                  },
                  __typename: 'ConfigTypeField',
                },
                __typename: 'Resource',
              },
            ],
            __typename: 'Mode',
          },
        ],
        __typename: 'Pipeline',
      },
    },
  },
};

export const LaunchAssetLoaderResourceJob8Mock: MockedResponse<LaunchAssetLoaderResourceQuery> = {
  request: {
    query: LAUNCH_ASSET_LOADER_RESOURCE_QUERY,
    variables: {
      pipelineName: '__ASSET_JOB_8',
      repositoryLocationName: 'test.py',
      repositoryName: 'repo',
    },
  },
  result: {
    data: {
      __typename: 'Query',
      partitionSetsOrError: {
        results: [
          {
            id: '129179973a9144278c2429d3ba680bf0f809a59b',
            name: '__ASSET_JOB_8_partition_set',
            __typename: 'PartitionSet',
          },
        ],
        __typename: 'PartitionSets',
      },
      pipelineOrError: {
        id: '8689a9dcd052f769b73d73dfe57e89065dac369d',
        modes: [
          {
            id: '719d9b2c592b98ae0f4a7ec570cae0a06667db31-default',
            resources: [
              {
                name: 'io_manager',
                description:
                  'Built-in filesystem IO manager that stores and retrieves values using pickling.',
                configField: {
                  name: 'config',
                  isRequired: false,
                  configType: {
                    __typename: 'CompositeConfigType',
                    key: 'Shape.18b2faaf1efd505374f7f25fcb61ed59bd5be851',
                    description: null,
                    isSelector: false,
                    typeParamKeys: [],
                    fields: [
                      {
                        name: 'base_dir',
                        description: null,
                        isRequired: false,
                        configTypeKey: 'StringSourceType',
                        defaultValueAsJson: null,
                        __typename: 'ConfigTypeField',
                      },
                    ],
                    recursiveConfigTypes: [
                      {
                        __typename: 'CompositeConfigType',
                        key: 'Selector.2571019f1a5201853d11032145ac3e534067f214',
                        description: null,
                        isSelector: true,
                        typeParamKeys: [],
                        fields: [
                          {
                            name: 'env',
                            description: null,
                            isRequired: true,
                            configTypeKey: 'String',
                            defaultValueAsJson: null,
                            __typename: 'ConfigTypeField',
                          },
                        ],
                      },
                      {
                        __typename: 'RegularConfigType',
                        givenName: 'String',
                        key: 'String',
                        description: '',
                        isSelector: false,
                        typeParamKeys: [],
                      },
                      {
                        __typename: 'ScalarUnionConfigType',
                        key: 'StringSourceType',
                        description: null,
                        isSelector: false,
                        typeParamKeys: [
                          'String',
                          'Selector.2571019f1a5201853d11032145ac3e534067f214',
                        ],
                        scalarTypeKey: 'String',
                        nonScalarTypeKey: 'Selector.2571019f1a5201853d11032145ac3e534067f214',
                      },
                    ],
                  },
                  __typename: 'ConfigTypeField',
                },
                __typename: 'Resource',
              },
            ],
            __typename: 'Mode',
          },
        ],
        __typename: 'Pipeline',
      },
    },
  },
};

export const LaunchAssetLoaderResourceMyAssetJobMock: MockedResponse<LaunchAssetLoaderResourceQuery> = {
  request: {
    query: LAUNCH_ASSET_LOADER_RESOURCE_QUERY,
    variables: {
      pipelineName: 'my_asset_job',
      repositoryLocationName: 'test.py',
      repositoryName: 'repo',
    },
  },
  result: {
    data: {
      __typename: 'Query',
      partitionSetsOrError: {
        results: [
          {
            id: '129179973a9144278c2429d3ba680bf0f809a59b',
            name: 'my_asset_job_partition_set',
            __typename: 'PartitionSet',
          },
        ],
        __typename: 'PartitionSets',
      },
      pipelineOrError: {
        id: '8689a9dcd052f769b73d73dfe57e89065dac369d',
        modes: [
          {
            __typename: 'Mode',
            id: '719d9b2c592b98ae0f4a7ec570cae0a06667db31-default',
            resources: [],
          },
        ],
        __typename: 'Pipeline',
      },
    },
  },
};

export const LaunchAssetLoaderAssetDailyWeeklyMock: MockedResponse<LaunchAssetLoaderQuery> = {
  request: {
    query: LAUNCH_ASSET_LOADER_QUERY,
    variables: {
      assetKeys: [{path: ['asset_daily']}, {path: ['asset_weekly']}],
    },
  },
  result: {
    data: {
      __typename: 'Query',
      assetNodes: [
        {
          ...ASSET_DAILY,
          requiredResources: [],
          partitionDefinition: {
            name: 'Foo',
            type: PartitionDefinitionType.TIME_WINDOW,
            description: 'Daily, starting 2020-01-01 UTC.',
            dimensionTypes: [buildDimensionDefinitionType({name: 'default'})],
            __typename: 'PartitionDefinition',
          },
          configField: {
            name: 'config',
            isRequired: false,
            configType: {
              __typename: 'RegularConfigType',
              givenName: 'Any',
              key: 'Any',
              description: null,
              isSelector: false,
              typeParamKeys: [],
              recursiveConfigTypes: [],
            },
            __typename: 'ConfigTypeField',
          },
          __typename: 'AssetNode',
        },
        {
          ...ASSET_WEEKLY,
          requiredResources: [],
          partitionDefinition: {
            name: 'Foo',
            type: PartitionDefinitionType.TIME_WINDOW,
            description: 'Weekly, starting 2020-01-01 UTC.',
            dimensionTypes: [buildDimensionDefinitionType({name: 'default'})],
            __typename: 'PartitionDefinition',
          },
          configField: {
            name: 'config',
            isRequired: false,
            configType: {
              __typename: 'RegularConfigType',
              givenName: 'Any',
              key: 'Any',
              description: null,
              isSelector: false,
              typeParamKeys: [],
              recursiveConfigTypes: [],
            },
            __typename: 'ConfigTypeField',
          },
          __typename: 'AssetNode',
        },
      ],
      assetNodeDefinitionCollisions: [],
    },
  },
};

export const LaunchAssetCheckUpstreamWeeklyRootMock: MockedResponse<LaunchAssetCheckUpstreamQuery> = {
  request: {
    query: LAUNCH_ASSET_CHECK_UPSTREAM_QUERY,
    variables: {
      assetKeys: [{path: ['asset_weekly_root']}],
    },
  },
  result: {
    data: {
      __typename: 'Query',
      assetNodes: [
        {
          id: 'test.py.repo.["asset_weekly_root"]',
          assetKey: {
            path: ['asset_weekly_root'],
            __typename: 'AssetKey',
          },
          isSource: false,
          opNames: ['asset_weekly_root'],
          graphName: null,
          assetMaterializations: [
            {
              runId: '8fec6fcd-7a05-4f1c-8cf8-4bfd6965eeba',
              __typename: 'MaterializationEvent',
            },
          ],
          __typename: 'AssetNode',
        },
      ],
    },
  },
};

export function buildConfigPartitionSelectionLatestPartitionMock(
  partitionName: string,
  partitionSetName: string,
): MockedResponse<ConfigPartitionSelectionQuery> {
  return {
    request: {
      query: CONFIG_PARTITION_SELECTION_QUERY,
      variables: {
        partitionName,
        partitionSetName,
        repositorySelector: {
          repositoryLocationName: 'test.py',
          repositoryName: 'repo',
        },
      },
    },
    result: {
      data: {
        __typename: 'Query',
        partitionSetOrError: {
          __typename: 'PartitionSet',
          id: '5b10aae97b738c48a4262b1eca530f89b13e9afc',
          partition: {
            name: '2023-03-14',
            solidSelection: null,
            runConfigOrError: {
              yaml: '{}\n',
              __typename: 'PartitionRunConfig',
            },
            mode: 'default',
            tagsOrError: {
              results: [
                {
                  key: 'dagster/partition',
                  value: partitionName,
                  __typename: 'PipelineTag',
                },
                {
                  key: 'dagster/partition_set',
                  value: partitionSetName,
                  __typename: 'PipelineTag',
                },
              ],
              __typename: 'PartitionTags',
            },
            __typename: 'Partition',
          },
        },
      },
    },
  };
}

type LaunchAssetLoaderQueryAssetNode = LaunchAssetLoaderQuery['assetNodes'][0];

const ASSET_DAILY_LOADER_RESULT: LaunchAssetLoaderQueryAssetNode = {
  ...ASSET_DAILY,
  requiredResources: [],
  partitionDefinition: {
    name: 'Foo',
    type: PartitionDefinitionType.TIME_WINDOW,
    description: 'Daily, starting 2020-01-01 UTC.',
    dimensionTypes: [buildDimensionDefinitionType({name: 'default'})],
    __typename: 'PartitionDefinition',
  },
  configField: {
    name: 'config',
    isRequired: false,
    configType: {
      __typename: 'RegularConfigType',
      givenName: 'Any',
      key: 'Any',
      description: null,
      isSelector: false,
      typeParamKeys: [],
      recursiveConfigTypes: [],
    },
    __typename: 'ConfigTypeField',
  },
  __typename: 'AssetNode',
};

const ASSET_WEEKLY_LOADER_RESULT: LaunchAssetLoaderQueryAssetNode = {
  ...ASSET_WEEKLY,
  requiredResources: [],
  partitionDefinition: {
    name: 'Foo',
    type: PartitionDefinitionType.TIME_WINDOW,
    description: 'Weekly, starting 2020-01-01 UTC.',
    dimensionTypes: [buildDimensionDefinitionType({name: 'default'})],
    __typename: 'PartitionDefinition',
  },

  dependencyKeys: [
    {
      __typename: 'AssetKey',
      path: ['asset_daily'],
    },
    {
      __typename: 'AssetKey',
      path: ['asset_weekly_root'],
    },
  ],
  configField: {
    name: 'config',
    isRequired: false,
    configType: {
      __typename: 'RegularConfigType',
      givenName: 'Any',
      key: 'Any',
      description: null,
      isSelector: false,
      typeParamKeys: [],
      recursiveConfigTypes: [],
    },
    __typename: 'ConfigTypeField',
  },
  __typename: 'AssetNode',
};

const ASSET_WEEKLY_ROOT_LOADER_RESULT: LaunchAssetLoaderQueryAssetNode = {
  ...ASSET_WEEKLY_ROOT,
  requiredResources: [],
  partitionDefinition: {
    name: 'Foo',
    type: PartitionDefinitionType.TIME_WINDOW,
    description: 'Weekly, starting 2020-01-01 UTC.',
    dimensionTypes: [buildDimensionDefinitionType({name: 'default'})],
    __typename: 'PartitionDefinition',
  },
  configField: {
    name: 'config',
    isRequired: false,
    configType: {
      __typename: 'RegularConfigType',
      givenName: 'Any',
      key: 'Any',
      description: null,
      isSelector: false,
      typeParamKeys: [],
      recursiveConfigTypes: [],
    },
    __typename: 'ConfigTypeField',
  },
  __typename: 'AssetNode',
};

const UNPARTITIONED_ASSET_LOADER_RESULT: LaunchAssetLoaderQueryAssetNode = {
  ...UNPARTITIONED_ASSET,
  requiredResources: [],
  partitionDefinition: null,
  configField: {
    name: 'config',
    isRequired: false,
    configType: {
      __typename: 'RegularConfigType',
      givenName: 'Any',
      key: 'Any',
      description: null,
      isSelector: false,
      typeParamKeys: [],
      recursiveConfigTypes: [],
    },
    __typename: 'ConfigTypeField',
  },
  __typename: 'AssetNode',
};
const UNPARTITIONED_ASSET_OTHER_REPO_LOADER_RESULT: LaunchAssetLoaderQueryAssetNode = {
  ...UNPARTITIONED_ASSET_OTHER_REPO,
  requiredResources: [],
  partitionDefinition: null,
  configField: {
    name: 'config',
    isRequired: false,
    configType: {
      __typename: 'RegularConfigType',
      givenName: 'Any',
      key: 'Any',
      description: null,
      isSelector: false,
      typeParamKeys: [],
      recursiveConfigTypes: [],
    },
    __typename: 'ConfigTypeField',
  },
  __typename: 'AssetNode',
};

const UNPARTITIONED_ASSET_WITH_REQUIRED_CONFIG_LOADER_RESULT: LaunchAssetLoaderQueryAssetNode = {
  ...UNPARTITIONED_ASSET_WITH_REQUIRED_CONFIG,
  requiredResources: [],
  partitionDefinition: null,
  configField: {
    name: 'config',
    isRequired: true,
    configType: {
      __typename: 'RegularConfigType',
      givenName: 'Any',
      key: 'Any',
      description: null,
      isSelector: false,
      typeParamKeys: [],
      recursiveConfigTypes: [],
    },
    __typename: 'ConfigTypeField',
  },
  __typename: 'AssetNode',
};

export const LOADER_RESULTS = [
  ASSET_DAILY_LOADER_RESULT,
  ASSET_WEEKLY_LOADER_RESULT,
  ASSET_WEEKLY_ROOT_LOADER_RESULT,
  UNPARTITIONED_ASSET_LOADER_RESULT,
  UNPARTITIONED_ASSET_WITH_REQUIRED_CONFIG_LOADER_RESULT,
  UNPARTITIONED_ASSET_OTHER_REPO_LOADER_RESULT,
];

export const PartitionHealthAssetMocks = [
  PartitionHealthAssetWeeklyRootMock,
  PartitionHealthAssetWeeklyMock,
  PartitionHealthAssetDailyMock,
];

export function buildLaunchAssetLoaderMock(
  assetKeys: AssetKeyInput[],
): MockedResponse<LaunchAssetLoaderQuery> {
  return {
    request: {
      query: LAUNCH_ASSET_LOADER_QUERY,
      variables: {
        assetKeys: assetKeys.map((a) => ({path: a.path})),
      },
    },
    result: {
      data: {
        __typename: 'Query',
        assetNodeDefinitionCollisions: [],
        assetNodes: LOADER_RESULTS.filter((a) =>
          assetKeys.some((k) => tokenForAssetKey(k) === tokenForAssetKey(a.assetKey)),
        ),
      },
    },
  };
}

export function buildExpectedLaunchBackfillMutation(
  backfillParams: LaunchBackfillParams,
): MockedResponse<LaunchPartitionBackfillMutation> {
  return {
    request: {
      query: LAUNCH_PARTITION_BACKFILL_MUTATION,
      variables: {backfillParams},
    },
    result: jest.fn(() => ({
      data: {
        __typename: 'Mutation',
        launchPartitionBackfill: {__typename: 'LaunchBackfillSuccess', backfillId: 'backfillid'},
      },
    })),
  };
}

export function buildExpectedLaunchSingleRunMutation(
  executionParams: LaunchPipelineExecutionMutationVariables['executionParams'],
): MockedResponse<LaunchPipelineExecutionMutation> {
  return {
    request: {
      query: LAUNCH_PIPELINE_EXECUTION_MUTATION,
      variables: {executionParams},
    },
    result: jest.fn(() => ({
      data: {
        __typename: 'Mutation',
        launchPipelineExecution: {
          __typename: 'LaunchRunSuccess',
          run: {
            __typename: 'Run',
            runId: 'RUN_ID',
            id: 'RUN_ID',
            pipelineName: executionParams['selector']['pipelineName']!,
          },
        },
      },
    })),
  };
}
