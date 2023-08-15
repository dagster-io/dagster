import {MockedResponse} from '@apollo/client/testing';

import {AssetGraphQuery} from '../../asset-graph/types/useAssetGraphData.types';
import {ASSET_GRAPH_QUERY} from '../../asset-graph/useAssetGraphData';
import {ASSET_VIEW_DEFINITION_QUERY} from '../AssetView';
import {AssetViewDefinitionQuery} from '../types/AssetView.types';

export const LatestMaterializationTimestamp = '1671568270073';

export const AssetGraphEmpty: MockedResponse<AssetGraphQuery> = {
  request: {
    query: ASSET_GRAPH_QUERY,
    variables: {},
  },
  result: {
    data: {
      __typename: 'Query',
      assetNodes: [],
    },
  },
};

export const AssetViewDefinitionNonSDA: MockedResponse<AssetViewDefinitionQuery> = {
  request: {
    query: ASSET_VIEW_DEFINITION_QUERY,
    variables: {
      assetKey: {path: ['non_sda_asset']},
    },
  },
  result: {
    data: {
      __typename: 'Query',
      assetOrError: {
        id: '["non_sda_asset"]',
        key: {
          path: ['non_sda_asset'],
          __typename: 'AssetKey',
        },
        assetMaterializations: [
          {
            timestamp: LatestMaterializationTimestamp,
            __typename: 'MaterializationEvent',
          },
        ],
        definition: null,
        __typename: 'Asset',
      },
    },
  },
};

export const AssetViewDefinitionSourceAsset: MockedResponse<AssetViewDefinitionQuery> = {
  request: {
    query: ASSET_VIEW_DEFINITION_QUERY,
    variables: {
      assetKey: {path: ['observable_source_asset']},
    },
  },
  result: {
    data: {
      __typename: 'Query',
      assetOrError: {
        id: 'test.py.repo.["observable_source_asset"]',
        key: {
          path: ['observable_source_asset'],
          __typename: 'AssetKey',
        },
        assetMaterializations: [],
        definition: {
          id: 'test.py.repo.["observable_source_asset"]',
          groupName: 'GROUP3',
          partitionDefinition: null,
          partitionKeysByDimension: [],
          repository: {
            id: '4d0b1967471d9a4682ccc97d12c1c508d0d9c2e1',
            name: 'repo',
            location: {
              id: 'test.py',
              name: 'test.py',
              __typename: 'RepositoryLocation',
            },
            __typename: 'Repository',
          },
          jobs: [],
          __typename: 'AssetNode',
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
          isSource: true,
          assetKey: {
            path: ['observable_source_asset'],
            __typename: 'AssetKey',
          },
          metadataEntries: [],
          type: null,
          requiredResources: [
            {
              __typename: 'ResourceRequirement',
              resourceKey: 'foo',
            },
          ],
        },
        __typename: 'Asset',
      },
    },
  },
};

export const AssetViewDefinitionSDA: MockedResponse<AssetViewDefinitionQuery> = {
  request: {
    query: ASSET_VIEW_DEFINITION_QUERY,
    variables: {
      assetKey: {path: ['sda_asset']},
    },
  },
  result: {
    data: {
      __typename: 'Query',
      assetOrError: {
        id: 'test.py.repo.["sda_asset"]',
        key: {
          path: ['sda_asset'],
          __typename: 'AssetKey',
        },
        assetMaterializations: [],
        definition: {
          id: 'test.py.repo.["sda_asset"]',
          groupName: 'GROUP3',
          partitionDefinition: null,
          partitionKeysByDimension: [],
          repository: {
            id: '4d0b1967471d9a4682ccc97d12c1c508d0d9c2e1',
            name: 'repo',
            location: {
              id: 'test.py',
              name: 'test.py',
              __typename: 'RepositoryLocation',
            },
            __typename: 'Repository',
          },
          jobs: [],
          __typename: 'AssetNode',
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
          isSource: false,
          assetKey: {
            path: ['sda_asset'],
            __typename: 'AssetKey',
          },
          metadataEntries: [],
          type: null,
          requiredResources: [
            {
              __typename: 'ResourceRequirement',
              resourceKey: 'foo',
            },
          ],
        },
        __typename: 'Asset',
      },
    },
  },
};
