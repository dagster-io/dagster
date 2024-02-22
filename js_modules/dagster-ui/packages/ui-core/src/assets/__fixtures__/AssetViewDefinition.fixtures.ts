import {
  buildAsset,
  buildAssetKey,
  buildAssetNode,
  buildMaterializationEvent,
  buildRepository,
  buildRepositoryLocation,
  buildResourceRequirement,
} from '../../graphql/types';
import {ASSET_VIEW_DEFINITION_QUERY} from '../AssetView';
import {buildQueryMock} from '../AutoMaterializePolicyPage/__fixtures__/AutoMaterializePolicyPage.fixtures';
import {
  AssetViewDefinitionQuery,
  AssetViewDefinitionQueryVariables,
} from '../types/AssetView.types';

export const LatestMaterializationTimestamp = '1671568270073';
export const AssetViewDefinitionNonSDA = buildQueryMock<
  AssetViewDefinitionQuery,
  AssetViewDefinitionQueryVariables
>({
  query: ASSET_VIEW_DEFINITION_QUERY,
  variables: {
    assetKey: {path: ['non_sda_asset']},
  },
  data: {
    assetOrError: buildAsset({
      id: '["non_sda_asset"]',
      key: buildAssetKey({
        path: ['non_sda_asset'],
      }),
      assetMaterializations: [
        buildMaterializationEvent({
          timestamp: LatestMaterializationTimestamp,
        }),
      ],
      definition: null,
    }),
  },
});

export const AssetViewDefinitionSourceAsset = buildQueryMock<
  AssetViewDefinitionQuery,
  AssetViewDefinitionQueryVariables
>({
  query: ASSET_VIEW_DEFINITION_QUERY,
  variables: {
    assetKey: {path: ['observable_source_asset']},
  },
  data: {
    assetOrError: buildAsset({
      id: 'test.py.repo.["observable_source_asset"]',
      key: buildAssetKey({
        path: ['observable_source_asset'],
      }),
      assetMaterializations: [],
      definition: buildAssetNode({
        id: 'test.py.repo.["observable_source_asset"]',
        groupName: 'GROUP3',
        backfillPolicy: null,
        partitionDefinition: null,

        partitionKeysByDimension: [],
        repository: buildRepository({
          id: '4d0b1967471d9a4682ccc97d12c1c508d0d9c2e1',
          name: 'repo',
          location: buildRepositoryLocation({
            id: 'test.py',
            name: 'test.py',
          }),
        }),
        description: null,
        graphName: null,
        opNames: [],
        opVersion: null,
        jobNames: ['__ASSET_JOB'],
        configField: null,
        autoMaterializePolicy: null,
        freshnessPolicy: null,
        hasMaterializePermission: true,
        computeKind: null,
        isPartitioned: false,
        isObservable: true,
        isExecutable: true,
        isSource: true,
        metadataEntries: [],
        type: null,
        requiredResources: [buildResourceRequirement({resourceKey: 'foo'})],
        targetingInstigators: [],
      }),
    }),
  },
});

export const AssetViewDefinitionSDA = buildQueryMock<
  AssetViewDefinitionQuery,
  AssetViewDefinitionQueryVariables
>({
  query: ASSET_VIEW_DEFINITION_QUERY,
  variables: {
    assetKey: {path: ['sda_asset']},
  },
  data: {
    assetOrError: buildAsset({
      id: 'test.py.repo.["sda_asset"]',
      key: buildAssetKey({
        path: ['sda_asset'],
      }),
      assetMaterializations: [],
      definition: buildAssetNode({
        id: 'test.py.repo.["sda_asset"]',
        groupName: 'GROUP3',
        backfillPolicy: null,
        partitionDefinition: null,
        partitionKeysByDimension: [],
        repository: buildRepository({
          id: '4d0b1967471d9a4682ccc97d12c1c508d0d9c2e1',
          name: 'repo',
          location: buildRepositoryLocation({
            id: 'test.py',
            name: 'test.py',
          }),
        }),
        description: null,
        graphName: null,
        opNames: [],
        opVersion: null,
        jobNames: ['__ASSET_JOB'],
        configField: null,
        autoMaterializePolicy: null,
        freshnessPolicy: null,
        hasMaterializePermission: true,
        computeKind: null,
        isPartitioned: false,
        isObservable: false,
        isExecutable: true,
        isSource: false,
        metadataEntries: [],
        type: null,
        requiredResources: [buildResourceRequirement({resourceKey: 'foo'})],
        targetingInstigators: [],
      }),
    }),
  },
});
