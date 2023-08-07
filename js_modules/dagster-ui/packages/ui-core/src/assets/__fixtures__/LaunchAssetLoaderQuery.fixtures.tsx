import {MockedResponse} from '@apollo/client/testing';

import {
  AssetNode,
  PartitionDefinitionType,
  buildAssetKey,
  buildAssetNode,
  buildConfigTypeField,
  buildDimensionDefinitionType,
  buildPartitionDefinition,
  buildRegularConfigType,
  buildRepository,
  buildRepositoryLocation,
} from '../../graphql/types';
import {LAUNCH_ASSET_LOADER_QUERY} from '../LaunchAssetExecutionButton';
import {LaunchAssetLoaderQuery} from '../types/LaunchAssetExecutionButton.types';

export const assetNodes: AssetNode[] = [
  buildAssetNode({
    id: 'assets_dynamic_partitions.__repository__.["release_files"]',
    opNames: ['release_files'],
    jobNames: ['__ASSET_JOB_0'],
    graphName: null,
    hasMaterializePermission: true,
    partitionDefinition: buildPartitionDefinition({
      type: PartitionDefinitionType.DYNAMIC,
      name: 'Foo',
      description: 'Dynamic partitions definition releases',
      dimensionTypes: [
        buildDimensionDefinitionType({
          name: 'default',
        }),
      ],
    }),
    isObservable: false,
    isSource: false,
    assetKey: buildAssetKey({
      path: ['release_files'],
    }),
    dependencyKeys: [
      buildAssetKey({
        path: ['release_zips'],
      }),
    ],
    repository: buildRepository({
      id: 'd2e5e8b7989e1da5fd8f505e6a968a03b24d40f4',
      name: '__repository__',
      location: buildRepositoryLocation({
        id: 'assets_dynamic_partitions',
        name: 'assets_dynamic_partitions',
      }),
    }),
    requiredResources: [],
    configField: buildConfigTypeField({
      name: 'config',
      isRequired: false,
      configType: buildRegularConfigType({
        recursiveConfigTypes: [],
        key: 'Any',
        description: null,
        isSelector: false,
        typeParamKeys: [],
        givenName: 'Any',
      }),
    }),
  }),
  buildAssetNode({
    id: 'assets_dynamic_partitions.__repository__.["release_files_metadata"]',
    opNames: ['release_files_metadata'],
    jobNames: ['__ASSET_JOB_0'],
    graphName: null,
    hasMaterializePermission: true,
    partitionDefinition: buildPartitionDefinition({
      type: PartitionDefinitionType.DYNAMIC,
      name: 'Foo',
      description: 'Dynamic partitions definition releases',
      dimensionTypes: [
        buildDimensionDefinitionType({
          name: 'default',
        }),
      ],
    }),
    isObservable: false,
    isSource: false,
    assetKey: buildAssetKey({
      path: ['release_files_metadata'],
    }),
    dependencyKeys: [
      buildAssetKey({
        path: ['release_files'],
      }),
    ],
    repository: buildRepository({
      id: 'd2e5e8b7989e1da5fd8f505e6a968a03b24d40f4',
      name: '__repository__',
      location: buildRepositoryLocation({
        id: 'assets_dynamic_partitions',
        name: 'assets_dynamic_partitions',
      }),
    }),
    requiredResources: [],
    configField: buildConfigTypeField({
      name: 'config',
      isRequired: false,
      configType: buildRegularConfigType({
        recursiveConfigTypes: [],
        key: 'Any',
        description: null,
        isSelector: false,
        typeParamKeys: [],
        givenName: 'Any',
      }),
    }),
  }),
  buildAssetNode({
    id: 'assets_dynamic_partitions.__repository__.["release_zips"]',
    opNames: ['release_zips'],
    jobNames: ['__ASSET_JOB_0'],
    graphName: null,
    hasMaterializePermission: true,
    partitionDefinition: buildPartitionDefinition({
      type: PartitionDefinitionType.DYNAMIC,
      name: 'Foo',
      description: 'Dynamic partitions definition releases',
      dimensionTypes: [
        buildDimensionDefinitionType({
          name: 'default',
        }),
      ],
    }),
    isObservable: false,
    isSource: false,
    assetKey: buildAssetKey({
      path: ['release_zips'],
    }),
    dependencyKeys: [
      buildAssetKey({
        path: ['releases_metadata'],
      }),
    ],
    repository: buildRepository({
      id: 'd2e5e8b7989e1da5fd8f505e6a968a03b24d40f4',
      name: '__repository__',
      location: buildRepositoryLocation({
        id: 'assets_dynamic_partitions',
        name: 'assets_dynamic_partitions',
      }),
    }),
    requiredResources: [],
    configField: buildConfigTypeField({
      name: 'config',
      isRequired: false,
      configType: buildRegularConfigType({
        recursiveConfigTypes: [],
        key: 'Any',
        description: null,
        isSelector: false,
        typeParamKeys: [],
        givenName: 'Any',
      }),
    }),
  }),
  buildAssetNode({
    id: 'assets_dynamic_partitions.__repository__.["releases_metadata"]',
    opNames: ['releases_metadata'],
    jobNames: ['__ASSET_JOB_0'],
    graphName: null,
    hasMaterializePermission: true,
    partitionDefinition: buildPartitionDefinition({
      type: PartitionDefinitionType.DYNAMIC,
      name: 'Foo',
      description: 'Dynamic partitions definition releases',
      dimensionTypes: [
        buildDimensionDefinitionType({
          name: 'default',
        }),
      ],
    }),
    isObservable: false,
    isSource: false,
    assetKey: buildAssetKey({
      path: ['releases_metadata'],
    }),
    dependencyKeys: [],
    repository: buildRepository({
      id: 'd2e5e8b7989e1da5fd8f505e6a968a03b24d40f4',
      name: '__repository__',
      location: buildRepositoryLocation({
        id: 'assets_dynamic_partitions',
        name: 'assets_dynamic_partitions',
      }),
    }),
    requiredResources: [],
    configField: buildConfigTypeField({
      name: 'config',
      isRequired: false,
      configType: buildRegularConfigType({
        recursiveConfigTypes: [],
        key: 'Any',
        description: null,
        isSelector: false,
        typeParamKeys: [],
        givenName: 'Any',
      }),
    }),
  }),
  buildAssetNode({
    id: 'assets_dynamic_partitions.__repository__.["releases_summary"]',
    opNames: ['releases_summary'],
    jobNames: ['__ASSET_JOB_0'],
    graphName: null,
    hasMaterializePermission: true,
    partitionDefinition: null,
    isObservable: false,
    isSource: false,
    assetKey: buildAssetKey({
      path: ['releases_summary'],
    }),
    dependencyKeys: [
      buildAssetKey({
        path: ['releases_metadata'],
      }),
      buildAssetKey({
        path: ['release_files_metadata'],
      }),
    ],
    repository: buildRepository({
      id: 'd2e5e8b7989e1da5fd8f505e6a968a03b24d40f4',
      name: '__repository__',
      location: buildRepositoryLocation({
        id: 'assets_dynamic_partitions',
        name: 'assets_dynamic_partitions',
      }),
    }),
    requiredResources: [],
    configField: buildConfigTypeField({
      name: 'config',
      isRequired: false,
      configType: buildRegularConfigType({
        recursiveConfigTypes: [],
        key: 'Any',
        description: null,
        isSelector: false,
        typeParamKeys: [],
        givenName: 'Any',
      }),
    }),
  }),
];

export const ReleasesWorkspace: MockedResponse<LaunchAssetLoaderQuery> = {
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
      __typename: 'Query' as const,
      assetNodes: assetNodes as any[],
      assetNodeDefinitionCollisions: [],
    },
  },
};
