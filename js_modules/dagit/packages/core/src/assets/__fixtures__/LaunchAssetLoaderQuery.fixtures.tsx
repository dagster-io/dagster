import {MockedResponse} from '@apollo/client/testing';

import {PartitionDefinitionType} from '../../graphql/types';
import {LAUNCH_ASSET_LOADER_QUERY} from '../LaunchAssetExecutionButton';
import {LaunchAssetLoaderQuery} from '../types/LaunchAssetExecutionButton.types';

export const ReleasesWorkspace_RAW = {
  request: {
    query: LAUNCH_ASSET_LOADER_QUERY,
    variables: {
      assetKeys: [
        {
          path: ['release_files'],
        },
        {
          path: ['release_files_metadata'],
        },
        {
          path: ['release_zips'],
        },
        {
          path: ['releases_metadata'],
        },
        {
          path: ['releases_summary'],
        },
      ],
    },
  },
  result: {
    data: {
      __typename: 'DagitQuery' as const,
      assetNodes: [
        {
          __typename: 'AssetNode' as const,
          id: 'assets_dynamic_partitions.__repository__.["release_files"]',
          opNames: ['release_files'],
          jobNames: ['__ASSET_JOB_0'],
          graphName: null,
          hasMaterializePermission: true,
          partitionDefinition: {
            type: PartitionDefinitionType.DYNAMIC,
            name: 'Foo',
            __typename: 'PartitionDefinition' as const,
            description: 'Dynamic partitions definition releases',
            dimensionTypes: [
              {
                __typename: 'DimensionDefinitionType' as const,
                name: 'default',
              },
            ],
          },
          isObservable: false,
          isSource: false,
          assetKey: {
            __typename: 'AssetKey' as const,
            path: ['release_files'],
          },
          dependencyKeys: [
            {
              __typename: 'AssetKey' as const,
              path: ['release_zips'],
            },
          ],
          repository: {
            __typename: 'Repository' as const,
            id: 'd2e5e8b7989e1da5fd8f505e6a968a03b24d40f4',
            name: '__repository__',
            location: {
              __typename: 'RepositoryLocation' as const,
              id: 'assets_dynamic_partitions',
              name: 'assets_dynamic_partitions',
            },
          },
          requiredResources: [],
          configField: {
            __typename: 'ConfigTypeField' as const,
            name: 'config',
            isRequired: false,
            configType: {
              __typename: 'RegularConfigType' as const,
              recursiveConfigTypes: [],
              key: 'Any',
              description: null,
              isSelector: false,
              typeParamKeys: [],
              givenName: 'Any',
            },
          },
        },
        {
          __typename: 'AssetNode' as const,
          id: 'assets_dynamic_partitions.__repository__.["release_files_metadata"]',
          opNames: ['release_files_metadata'],
          jobNames: ['__ASSET_JOB_0'],
          graphName: null,
          hasMaterializePermission: true,
          partitionDefinition: {
            type: PartitionDefinitionType.DYNAMIC,
            name: 'Foo',
            __typename: 'PartitionDefinition' as const,
            description: 'Dynamic partitions definition releases',
            dimensionTypes: [
              {
                __typename: 'DimensionDefinitionType' as const,
                name: 'default',
              },
            ],
          },
          isObservable: false,
          isSource: false,
          assetKey: {
            __typename: 'AssetKey' as const,
            path: ['release_files_metadata'],
          },
          dependencyKeys: [
            {
              __typename: 'AssetKey' as const,
              path: ['release_files'],
            },
          ],
          repository: {
            __typename: 'Repository' as const,
            id: 'd2e5e8b7989e1da5fd8f505e6a968a03b24d40f4',
            name: '__repository__',
            location: {
              __typename: 'RepositoryLocation' as const,
              id: 'assets_dynamic_partitions',
              name: 'assets_dynamic_partitions',
            },
          },
          requiredResources: [],
          configField: {
            __typename: 'ConfigTypeField' as const,
            name: 'config',
            isRequired: false,
            configType: {
              __typename: 'RegularConfigType' as const,
              recursiveConfigTypes: [],
              key: 'Any',
              description: null,
              isSelector: false,
              typeParamKeys: [],
              givenName: 'Any',
            },
          },
        },
        {
          __typename: 'AssetNode' as const,
          id: 'assets_dynamic_partitions.__repository__.["release_zips"]',
          opNames: ['release_zips'],
          jobNames: ['__ASSET_JOB_0'],
          graphName: null,
          hasMaterializePermission: true,
          partitionDefinition: {
            type: PartitionDefinitionType.DYNAMIC,
            name: 'Foo',
            __typename: 'PartitionDefinition' as const,
            description: 'Dynamic partitions definition releases',
            dimensionTypes: [
              {
                __typename: 'DimensionDefinitionType' as const,
                name: 'default',
              },
            ],
          },
          isObservable: false,
          isSource: false,
          assetKey: {
            __typename: 'AssetKey' as const,
            path: ['release_zips'],
          },
          dependencyKeys: [
            {
              __typename: 'AssetKey' as const,
              path: ['releases_metadata'],
            },
          ],
          repository: {
            __typename: 'Repository' as const,
            id: 'd2e5e8b7989e1da5fd8f505e6a968a03b24d40f4',
            name: '__repository__',
            location: {
              __typename: 'RepositoryLocation' as const,
              id: 'assets_dynamic_partitions',
              name: 'assets_dynamic_partitions',
            },
          },
          requiredResources: [],
          configField: {
            __typename: 'ConfigTypeField' as const,
            name: 'config',
            isRequired: false,
            configType: {
              __typename: 'RegularConfigType' as const,
              recursiveConfigTypes: [],
              key: 'Any',
              description: null,
              isSelector: false,
              typeParamKeys: [],
              givenName: 'Any',
            },
          },
        },
        {
          __typename: 'AssetNode' as const,
          id: 'assets_dynamic_partitions.__repository__.["releases_metadata"]',
          opNames: ['releases_metadata'],
          jobNames: ['__ASSET_JOB_0'],
          graphName: null,
          hasMaterializePermission: true,
          partitionDefinition: {
            type: PartitionDefinitionType.DYNAMIC,
            name: 'Foo',
            __typename: 'PartitionDefinition' as const,
            description: 'Dynamic partitions definition releases',
            dimensionTypes: [
              {
                __typename: 'DimensionDefinitionType' as const,
                name: 'default',
              },
            ],
          },
          isObservable: false,
          isSource: false,
          assetKey: {
            __typename: 'AssetKey' as const,
            path: ['releases_metadata'],
          },
          dependencyKeys: [],
          repository: {
            __typename: 'Repository' as const,
            id: 'd2e5e8b7989e1da5fd8f505e6a968a03b24d40f4',
            name: '__repository__',
            location: {
              __typename: 'RepositoryLocation' as const,
              id: 'assets_dynamic_partitions',
              name: 'assets_dynamic_partitions',
            },
          },
          requiredResources: [],
          configField: {
            __typename: 'ConfigTypeField' as const,
            name: 'config',
            isRequired: false,
            configType: {
              __typename: 'RegularConfigType' as const,
              recursiveConfigTypes: [],
              key: 'Any',
              description: null,
              isSelector: false,
              typeParamKeys: [],
              givenName: 'Any',
            },
          },
        },
        {
          __typename: 'AssetNode' as const,
          id: 'assets_dynamic_partitions.__repository__.["releases_summary"]',
          opNames: ['releases_summary'],
          jobNames: ['__ASSET_JOB_0'],
          graphName: null,
          hasMaterializePermission: true,
          partitionDefinition: null,
          isObservable: false,
          isSource: false,
          assetKey: {
            __typename: 'AssetKey' as const,
            path: ['releases_summary'],
          },
          dependencyKeys: [
            {
              __typename: 'AssetKey' as const,
              path: ['releases_metadata'],
            },
            {
              __typename: 'AssetKey' as const,
              path: ['release_files_metadata'],
            },
          ],
          repository: {
            __typename: 'Repository' as const,
            id: 'd2e5e8b7989e1da5fd8f505e6a968a03b24d40f4',
            name: '__repository__',
            location: {
              __typename: 'RepositoryLocation' as const,
              id: 'assets_dynamic_partitions',
              name: 'assets_dynamic_partitions',
            },
          },
          requiredResources: [],
          configField: {
            __typename: 'ConfigTypeField' as const,
            name: 'config',
            isRequired: false,
            configType: {
              __typename: 'RegularConfigType' as const,
              recursiveConfigTypes: [],
              key: 'Any',
              description: null,
              isSelector: false,
              typeParamKeys: [],
              givenName: 'Any',
            },
          },
        },
      ],
      assetNodeDefinitionCollisions: [],
    },
  },
};

export const ReleasesWorkspace: MockedResponse<LaunchAssetLoaderQuery> = ReleasesWorkspace_RAW;
