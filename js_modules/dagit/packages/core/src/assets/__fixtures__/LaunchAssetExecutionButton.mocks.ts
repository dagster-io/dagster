import {MockedResponse} from '@apollo/client/testing';

import {AssetNodeForGraphQueryFragment} from '../../asset-graph/types/useAssetGraphData.types';
import {PartitionDefinitionType, PartitionRangeStatus} from '../../graphql/types';
import {LAUNCH_ASSET_CHOOSE_PARTITIONS_QUERY} from '../LaunchAssetChoosePartitionsDialog';
import {LAUNCH_ASSET_LOADER_QUERY} from '../LaunchAssetExecutionButton';
import {LaunchAssetChoosePartitionsQuery} from '../types/LaunchAssetChoosePartitionsDialog.types';
import {LaunchAssetLoaderQuery} from '../types/LaunchAssetExecutionButton.types';
import {PartitionHealthQuery} from '../types/usePartitionHealthData.types';
import {PARTITION_HEALTH_QUERY} from '../usePartitionHealthData';

import {generateDailyTimePartitions} from './PartitionHealthSummary.mocks';

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
  jobNames: ['__ASSET_JOB_7'],
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

export const LaunchAssetChoosePartitionsMock: MockedResponse<LaunchAssetChoosePartitionsQuery> = {
  request: {
    query: LAUNCH_ASSET_CHOOSE_PARTITIONS_QUERY,
    variables: {},
  },
  result: {
    data: {
      __typename: 'DagitQuery',
      instance: {
        daemonHealth: {
          id: 'daemonHealth',
          daemonStatus: {id: 'BACKFILL', healthy: false, __typename: 'DaemonStatus'},
          __typename: 'DaemonHealth',
        },
        __typename: 'Instance',
        runQueuingSupported: false,
        runLauncher: {name: 'DefaultRunLauncher', __typename: 'RunLauncher'},
      },
    },
  },
};

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
      __typename: 'DagitQuery',
      assetNodeOrError: {
        id: 'test.py.repo.["asset_daily"]',
        partitionKeysByDimension: [
          {
            name: 'default',
            __typename: 'DimensionPartitionKeys',
            partitionKeys: ASSET_DAILY_PARTITION_KEYS,
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
              __typename: 'TimePartitionRange',
            },
            {
              status: PartitionRangeStatus.MATERIALIZED,
              startTime: 1663027200.0,
              endTime: 1667088000.0,
              startKey: '2022-09-13',
              endKey: '2022-10-29',
              __typename: 'TimePartitionRange',
            },
            {
              status: PartitionRangeStatus.MATERIALIZED,
              startTime: 1668816000.0,
              endTime: 1670803200.0,
              startKey: '2022-11-19',
              endKey: '2022-12-11',
              __typename: 'TimePartitionRange',
            },
            {
              status: PartitionRangeStatus.MATERIALIZED,
              startTime: 1671494400.0,
              endTime: 1674086400.0,
              startKey: '2022-12-20',
              endKey: '2023-01-18',
              __typename: 'TimePartitionRange',
            },
            {
              status: PartitionRangeStatus.MATERIALIZED,
              startTime: 1676851200.0,
              endTime: 1676937600.0,
              startKey: '2023-02-20',
              endKey: '2023-02-20',
              __typename: 'TimePartitionRange',
            },
          ],
          __typename: 'TimePartitions',
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
      __typename: 'DagitQuery',
      assetNodeOrError: {
        id: 'test.py.repo.["asset_weekly"]',
        partitionKeysByDimension: [
          {
            name: 'default',
            __typename: 'DimensionPartitionKeys',
            partitionKeys: generateDailyTimePartitions(
              new Date('2020-01-01'),
              new Date('2023-02-22'),
              7,
            ),
          },
        ],
        assetPartitionStatuses: {
          ranges: [],
          __typename: 'TimePartitions',
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
      __typename: 'DagitQuery',
      assetNodeOrError: {
        id: 'test.py.repo.["asset_weekly_root"]',
        partitionKeysByDimension: [
          {
            name: 'default',
            __typename: 'DimensionPartitionKeys',
            partitionKeys: generateDailyTimePartitions(
              new Date('2020-01-01'),
              new Date('2023-02-22'),
              7,
            ),
          },
        ],
        assetPartitionStatuses: {
          ranges: [],
          __typename: 'TimePartitions',
        },
        __typename: 'AssetNode',
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
      __typename: 'DagitQuery',
      assetNodes: [
        {
          ...ASSET_DAILY,
          requiredResources: [],
          partitionDefinition: {
            name: 'Foo',
            type: PartitionDefinitionType.TIME_WINDOW,
            description: 'Daily, starting 2020-01-01 UTC.',
            dimensionTypes: [{name: 'default', __typename: 'DimensionDefinitionType'}],
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
            dimensionTypes: [{name: 'default', __typename: 'DimensionDefinitionType'}],
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

export const LaunchAssetLoaderAssetDailyWeeklyRootsDifferentPartitioningMock: MockedResponse<LaunchAssetLoaderQuery> = {
  request: {
    query: LAUNCH_ASSET_LOADER_QUERY,
    variables: {
      assetKeys: [{path: ['asset_daily']}, {path: ['asset_weekly']}, {path: ['asset_weekly_root']}],
    },
  },
  result: {
    data: {
      __typename: 'DagitQuery',
      assetNodes: [
        {
          ...ASSET_DAILY,
          requiredResources: [],
          partitionDefinition: {
            name: 'Foo',
            type: PartitionDefinitionType.TIME_WINDOW,
            description: 'Daily, starting 2020-01-01 UTC.',
            dimensionTypes: [{name: 'default', __typename: 'DimensionDefinitionType'}],
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
            dimensionTypes: [{name: 'default', __typename: 'DimensionDefinitionType'}],
            __typename: 'PartitionDefinition',
          },

          dependencyKeys: [
            {
              __typename: 'AssetKey',
              path: ['asset_daily', 'asset_weekly_root'],
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
        },
        {
          ...ASSET_WEEKLY_ROOT,
          requiredResources: [],
          partitionDefinition: {
            name: 'Foo',
            type: PartitionDefinitionType.TIME_WINDOW,
            description: 'Weekly, starting 2020-01-01 UTC.',
            dimensionTypes: [{name: 'default', __typename: 'DimensionDefinitionType'}],
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
